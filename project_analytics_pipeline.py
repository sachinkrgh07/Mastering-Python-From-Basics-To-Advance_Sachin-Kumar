import argparse
import io
import os
from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


sns.set_theme(style="whitegrid")
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
    }
)


def ensure_output_dir(base_dir="eda_outputs"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(base_dir, f"run_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def load_dataset(source):
    if source.lower().endswith(".csv"):
        return pd.read_csv(source)
    if source.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(source)
    if source.lower().endswith((".db", ".sqlite", ".sqlite3")):
        import sqlite3

        conn = sqlite3.connect(source)
        try:
            df = pd.read_sql_query("SELECT * FROM transactions", conn)
        finally:
            conn.close()
        return df
    raise ValueError("Unsupported file type. Use CSV, Excel, or SQLite database.")


def find_column(df, candidates):
    lower_map = {c.lower().strip(): c for c in df.columns}
    for key in candidates:
        if key in lower_map:
            return lower_map[key]
    return None


def standardize_schema(df):
    original = df.copy()
    work = df.copy()

    aliases = {
        "Sales": ["sales", "revenue", "amount", "sale_amount"],
        "Profit": ["profit", "net_profit", "pnl", "margin_value"],
        "Quantity": ["quantity", "qty", "units", "volume", "count"],
        "Price": ["price", "unit_price", "rate", "mrp", "amount_per_unit"],
        "Items": ["items", "item", "item_name", "product", "description"],
        "Category": ["category", "segment", "class", "type", "group"],
        "Date": ["date", "order_date", "timestamp", "datetime"],
        "Flow": ["flow"],
    }

    mapped = {target: find_column(work, names) for target, names in aliases.items()}

    out = pd.DataFrame(index=work.index)

    flow_series = (
        work[mapped["Flow"]].astype(str).str.upper().str.strip()
        if mapped["Flow"] is not None
        else pd.Series(["IN"] * len(work), index=work.index)
    )
    flow_series = flow_series.where(flow_series.isin(["IN", "OUT"]), "IN")
    out["Flow"] = flow_series

    if mapped["Sales"] is not None:
        base_sales = pd.to_numeric(work[mapped["Sales"]], errors="coerce")
        out["Sales"] = np.where(flow_series.eq("IN"), base_sales, 0.0)
    elif find_column(work, ["amount"]) is not None:
        amt_col = find_column(work, ["amount"])
        amount = pd.to_numeric(work[amt_col], errors="coerce")
        out["Sales"] = np.where(flow_series.eq("IN"), amount, 0.0)
    else:
        raise ValueError("Could not infer Sales column.")

    if mapped["Profit"] is not None:
        out["Profit"] = pd.to_numeric(work[mapped["Profit"]], errors="coerce")
    elif find_column(work, ["amount"]) is not None:
        amt_col = find_column(work, ["amount"])
        amount = pd.to_numeric(work[amt_col], errors="coerce")
        out["Profit"] = np.where(flow_series.eq("IN"), amount, -amount)
    else:
        out["Profit"] = out["Sales"]

    if mapped["Quantity"] is not None:
        out["Quantity"] = pd.to_numeric(work[mapped["Quantity"]], errors="coerce")
    else:
        out["Quantity"] = 1.0

    if mapped["Price"] is not None:
        out["Price"] = pd.to_numeric(work[mapped["Price"]], errors="coerce")
    else:
        qty_nonzero = out["Quantity"].replace(0, np.nan)
        out["Price"] = (pd.to_numeric(out["Sales"], errors="coerce") / qty_nonzero).replace([np.inf, -np.inf], np.nan)
        out["Price"] = out["Price"].fillna(pd.to_numeric(out["Sales"], errors="coerce"))

    if mapped["Items"] is not None:
        out["Items"] = work[mapped["Items"]].astype(str)
    else:
        desc_col = find_column(work, ["description", "party_name", "narration"])
        out["Items"] = work[desc_col].astype(str) if desc_col is not None else "Item"

    if mapped["Category"] is not None:
        out["Category"] = work[mapped["Category"]].astype(str)
    else:
        out["Category"] = out["Flow"]

    if mapped["Date"] is not None:
        out["Date"] = pd.to_datetime(work[mapped["Date"]], errors="coerce")

    return out, original, mapped


def apply_date_range(df, start_date=None, end_date=None):
    if "Date" not in df.columns:
        return df, "No Date column found; full dataset used."

    filtered = df.copy()
    filtered["Date"] = pd.to_datetime(filtered["Date"], errors="coerce")
    filtered = filtered[filtered["Date"].notna()]

    note = "Full date span used."
    if start_date:
        start = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start):
            filtered = filtered[filtered["Date"] >= start]
            note = f"Start: {start.date()}"
    if end_date:
        end = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end):
            filtered = filtered[filtered["Date"] <= end]
            note = f"{note}, End: {end.date()}"

    return filtered, note


def classify_data_types(df):
    quantitative_discrete = []
    quantitative_continuous = []
    qualitative_nominal = []
    qualitative_ordinal = []

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            unique_count = df[col].nunique(dropna=True)
            if unique_count <= 20 or np.allclose(df[col].dropna() % 1, 0):
                quantitative_discrete.append(col)
            else:
                quantitative_continuous.append(col)
        else:
            unique_count = df[col].nunique(dropna=True)
            if unique_count <= 10:
                qualitative_ordinal.append(col)
            else:
                qualitative_nominal.append(col)

    return {
        "quantitative_discrete": quantitative_discrete,
        "quantitative_continuous": quantitative_continuous,
        "qualitative_nominal": qualitative_nominal,
        "qualitative_ordinal": qualitative_ordinal,
    }


def save_plot(out_dir, file_name):
    path = os.path.join(out_dir, file_name)
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def has_variation(series):
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return False
    return cleaned.nunique() > 1


def create_pdf_and_cleanup(image_paths, out_dir, pdf_name="eda_plots.pdf"):
    valid_images = sorted([p for p in image_paths if p and os.path.exists(p)])
    pdf_path = os.path.join(out_dir, pdf_name)

    if valid_images:
        with PdfPages(pdf_path) as pdf:
            for img_path in valid_images:
                image = plt.imread(img_path)
                fig = plt.figure(figsize=(11.69, 8.27))
                ax = fig.add_subplot(111)
                ax.imshow(image)
                ax.axis("off")
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)

        for img_path in valid_images:
            try:
                os.remove(img_path)
            except OSError:
                pass

    return pdf_path


def univariate_analysis(df, out_dir):
    numeric_targets = ["Sales", "Profit", "Quantity", "Price"]
    generated = []
    for col in numeric_targets:
        if col not in df.columns:
            continue
        if not has_variation(df[col]):
            continue

        plt.figure(figsize=(9, 4.8))
        sns.histplot(df[col].dropna(), kde=True, bins=30, color="#2563eb")
        plt.title(f"Histogram of {col}")
        plt.xlabel(col)
        plt.ylabel("Count")
        generated.append(save_plot(out_dir, f"univariate_hist_{col.lower()}.png"))

        plt.figure(figsize=(9, 4.8))
        sns.boxplot(x=df[col], color="#93c5fd")
        plt.title(f"Boxplot of {col}")
        plt.xlabel(col)
        generated.append(save_plot(out_dir, f"univariate_box_{col.lower()}.png"))
    return generated


def bivariate_analysis(df, out_dir):
    pairs = [("Sales", "Profit"), ("Price", "Quantity"), ("Quantity", "Sales"), ("Price", "Profit")]
    generated = []
    for x_col, y_col in pairs:
        if x_col not in df.columns or y_col not in df.columns:
            continue
        plot_df = df[[x_col, y_col] + (["Flow"] if "Flow" in df.columns else [])].dropna().copy()
        if "Flow" in plot_df.columns and (x_col == "Sales" or y_col == "Sales"):
            plot_df = plot_df[plot_df["Flow"].eq("IN")]
        if plot_df.empty or not has_variation(plot_df[x_col]) or not has_variation(plot_df[y_col]):
            continue

        plt.figure(figsize=(8.5, 5.5))
        sns.scatterplot(
            data=plot_df,
            x=x_col,
            y=y_col,
            alpha=0.75,
            hue="Flow" if "Flow" in plot_df.columns else None,
            palette="Set2",
        )
        plt.title(f"{x_col} vs {y_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        generated.append(save_plot(out_dir, f"bivariate_{x_col.lower()}_{y_col.lower()}.png"))

    corr_df = df.select_dtypes(include=np.number).corr(numeric_only=True)
    plt.figure(figsize=(9, 6.8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.4, annot_kws={"size": 9})
    plt.title("Correlation Matrix")
    generated.append(save_plot(out_dir, "bivariate_correlation_matrix.png"))
    return generated, corr_df


def multivariate_analysis(df, out_dir):
    generated = []
    cols = [c for c in ["Sales", "Profit", "Price", "Quantity"] if c in df.columns]
    if len(cols) >= 2:
        hue_col = "Flow" if "Flow" in df.columns else ("Category" if "Category" in df.columns else None)
        pairplot_df = df[cols + [hue_col]].dropna().copy() if hue_col else df[cols].dropna().copy()
        if len(pairplot_df) > 1:
            if len(pairplot_df) > 2000:
                pairplot_df = pairplot_df.sample(2000, random_state=42)
            pp = sns.pairplot(pairplot_df, vars=cols, hue=hue_col, corner=True)
            pp.fig.suptitle("Pair Plot", y=1.02)
            pairplot_path = os.path.join(out_dir, "multivariate_pairplot.png")
            pp.savefig(pairplot_path, dpi=140)
            plt.close("all")
            generated.append(pairplot_path)

    if all(c in df.columns for c in ["Sales", "Profit", "Price", "Items"]):
        pivot = (
            df.groupby("Items")[["Sales", "Profit", "Price"]]
            .mean(numeric_only=True)
            .sort_values("Sales", ascending=False)
            .head(15)
        )
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot, annot=True, cmap="YlGnBu", fmt=".2f", linewidths=0.4, annot_kws={"size": 8})
        plt.title("Sales, Profit, Price across Top Items (Mean)")
        generated.append(save_plot(out_dir, "multivariate_items_heatmap.png"))
    return generated


def operational_charts(df, out_dir):
    generated = []

    if "Date" in df.columns:
        ts = df.copy()
        ts["Date"] = pd.to_datetime(ts["Date"], errors="coerce")
        ts = ts[ts["Date"].notna()].copy()
        if not ts.empty:
            ts["Month"] = ts["Date"].dt.to_period("M").dt.to_timestamp()
            monthly = ts.groupby(["Month", "Flow"], dropna=False)["Profit"].sum().reset_index()
            plt.figure(figsize=(10.5, 5.5))
            sns.lineplot(data=monthly, x="Month", y="Profit", hue="Flow", marker="o", palette="Set1")
            plt.title("Monthly Profit Trend by Flow (IN/OUT)")
            plt.xlabel("Month")
            plt.ylabel("Profit")
            generated.append(save_plot(out_dir, "timeseries_monthly_profit_by_flow.png"))

    if all(c in df.columns for c in ["Items", "Profit"]):
        top_items = (
            df.groupby("Items", dropna=False)["Profit"]
            .sum()
            .sort_values(ascending=False)
            .head(12)
            .reset_index()
        )
        if not top_items.empty and has_variation(top_items["Profit"]):
            plt.figure(figsize=(10.5, 6.2))
            sns.barplot(data=top_items, y="Items", x="Profit", color="#4f46e5")
            plt.title("Top 12 Items by Net Profit")
            plt.xlabel("Net Profit")
            plt.ylabel("Items")
            generated.append(save_plot(out_dir, "items_top_profit_bar.png"))

    return generated


def handle_missing_data(df):
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]

    mean_filled = df.copy()
    median_filled = df.copy()
    mode_filled = df.copy()

    for col in numeric_cols:
        mean_filled[col] = mean_filled[col].fillna(mean_filled[col].mean())
        median_filled[col] = median_filled[col].fillna(median_filled[col].median())
        mode_val = mode_filled[col].mode(dropna=True)
        mode_filled[col] = mode_filled[col].fillna(mode_val.iloc[0] if not mode_val.empty else 0)

    for col in cat_cols:
        mode_val = df[col].mode(dropna=True)
        fill_value = mode_val.iloc[0] if not mode_val.empty else "Unknown"
        mean_filled[col] = mean_filled[col].fillna(fill_value)
        median_filled[col] = median_filled[col].fillna(fill_value)
        mode_filled[col] = mode_filled[col].fillna(fill_value)

    return mean_filled, median_filled, mode_filled


def detect_outliers_iqr(df, columns):
    outlier_summary = {}
    for col in columns:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            outlier_summary[col] = 0
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_summary[col] = int(((df[col] < lower) | (df[col] > upper)).sum())
    return outlier_summary


def spread_analysis(df):
    rows = []
    for col in ["Sales", "Profit", "Quantity", "Price"]:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        skew = series.skew()
        kurt = series.kurtosis()

        if abs(skew) < 0.5:
            dist = "Approximately Normal"
        elif skew > 0:
            dist = "Right Skewed"
        else:
            dist = "Left Skewed"

        rows.append(
            {
                "variable": col,
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "skewness": float(skew),
                "kurtosis": float(kurt),
                "distribution": dist,
            }
        )
    return pd.DataFrame(rows)


def reusable_eda_functions(df):
    info_buffer = io.StringIO()
    df.info(buf=info_buffer)
    return {
        "describe": df.describe(include="all").transpose(),
        "info": info_buffer.getvalue(),
        "isnull": df.isnull().sum().to_frame("missing_count"),
        "corr": df.select_dtypes(include=np.number).corr(numeric_only=True),
    }


def regression_and_models(df):
    model_df = df[["Sales", "Quantity", "Price", "Profit", "Flow"]].copy().dropna()

    if len(model_df) < 10:
        raise ValueError("Not enough rows for modeling. Need at least 10 clean rows.")

    model_df["Flow_IN"] = (model_df["Flow"].astype(str).str.upper() == "IN").astype(int)

    y_reg = model_df["Sales"]
    x_simple = model_df[["Quantity"]]
    x_multi = model_df[["Quantity", "Price", "Flow_IN"]]
    y_cls = (model_df["Profit"] > 0).astype(int)

    x_train_s, x_temp_s, y_train_s, y_temp_s = train_test_split(x_simple, y_reg, test_size=0.4, random_state=42)
    x_val_s, x_test_s, y_val_s, y_test_s = train_test_split(x_temp_s, y_temp_s, test_size=0.5, random_state=42)

    simple_model = LinearRegression().fit(x_train_s, y_train_s)
    pred_train_s = simple_model.predict(x_train_s)
    pred_val_s = simple_model.predict(x_val_s)
    pred_test_s = simple_model.predict(x_test_s)

    x_train_m, x_temp_m, y_train_m, y_temp_m = train_test_split(x_multi, y_reg, test_size=0.4, random_state=42)
    x_val_m, x_test_m, y_val_m, y_test_m = train_test_split(x_temp_m, y_temp_m, test_size=0.5, random_state=42)

    multi_model = LinearRegression().fit(x_train_m, y_train_m)
    pred_train_m = multi_model.predict(x_train_m)
    pred_val_m = multi_model.predict(x_val_m)
    pred_test_m = multi_model.predict(x_test_m)

    x_train_c, x_test_c, y_train_c, y_test_c = train_test_split(x_multi, y_cls, test_size=0.25, random_state=42)
    scaler = StandardScaler()
    x_train_c_scaled = scaler.fit_transform(x_train_c)
    x_test_c_scaled = scaler.transform(x_test_c)

    log_model = LogisticRegression(max_iter=500)
    log_model.fit(x_train_c_scaled, y_train_c)
    y_pred_c = log_model.predict(x_test_c_scaled)

    return {
        "simple": {
            "model": simple_model,
            "train": y_train_s,
            "val": y_val_s,
            "test": y_test_s,
            "pred_train": pred_train_s,
            "pred_val": pred_val_s,
            "pred_test": pred_test_s,
            "feature": "Quantity",
        },
        "multi": {
            "model": multi_model,
            "train": y_train_m,
            "val": y_val_m,
            "test": y_test_m,
            "pred_train": pred_train_m,
            "pred_val": pred_val_m,
            "pred_test": pred_test_m,
            "features": ["Quantity", "Price", "Flow_IN"],
        },
        "logistic": {
            "model": log_model,
            "y_test": y_test_c,
            "y_pred": y_pred_c,
        },
        "covariance": model_df[["Sales", "Quantity", "Price", "Flow_IN"]].cov(),
        "correlation": model_df[["Sales", "Quantity", "Price", "Flow_IN"]].corr(),
    }


def regression_metrics(y_true, y_pred):
    return {
        "MSE": float(mean_squared_error(y_true, y_pred)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
    }


def overfit_underfit_demo(df):
    mini = df[["Quantity", "Sales"]].dropna().sort_values("Quantity")
    if len(mini) < 10:
        return pd.DataFrame()

    x = mini[["Quantity"]].values
    y = mini["Sales"].values
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)

    rows = []
    for deg in [1, 2, 3, 5]:
        x_train_poly = np.hstack([x_train ** p for p in range(1, deg + 1)])
        x_test_poly = np.hstack([x_test ** p for p in range(1, deg + 1)])
        lr = LinearRegression().fit(x_train_poly, y_train)
        pred_train = lr.predict(x_train_poly)
        pred_test = lr.predict(x_test_poly)
        rows.append(
            {
                "degree": deg,
                "train_mse": float(mean_squared_error(y_train, pred_train)),
                "test_mse": float(mean_squared_error(y_test, pred_test)),
            }
        )
    return pd.DataFrame(rows)


def save_report(
    out_dir,
    source,
    df,
    mapped,
    type_info,
    corr_df,
    missing_before,
    outliers,
    spread_df,
    eda_obj,
    models,
    overfit_df,
    plots_pdf_path,
    date_filter_note,
):
    report_path = os.path.join(out_dir, "project_report.md")

    simple_train_metrics = regression_metrics(models["simple"]["train"], models["simple"]["pred_train"])
    simple_val_metrics = regression_metrics(models["simple"]["val"], models["simple"]["pred_val"])
    simple_test_metrics = regression_metrics(models["simple"]["test"], models["simple"]["pred_test"])

    multi_train_metrics = regression_metrics(models["multi"]["train"], models["multi"]["pred_train"])
    multi_val_metrics = regression_metrics(models["multi"]["val"], models["multi"]["pred_val"])
    multi_test_metrics = regression_metrics(models["multi"]["test"], models["multi"]["pred_test"])

    cls_acc = float(accuracy_score(models["logistic"]["y_test"], models["logistic"]["y_pred"]))
    cls_cm = confusion_matrix(models["logistic"]["y_test"], models["logistic"]["y_pred"])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Data Analytics Project Report\n\n")
        f.write(f"Source: `{source}`\n\n")

        f.write("## Task 1: Data Understanding\n")
        f.write(f"- Shape: {df.shape}\n")
        f.write(f"- Columns: {list(df.columns)}\n")
        f.write(f"- Mapped Columns: {mapped}\n")
        f.write(f"- Date Range Used: {date_filter_note}\n")
        f.write("\n### First 5 Rows\n")
        f.write(df.head().to_markdown(index=False))
        f.write("\n\n### Last 5 Rows\n")
        f.write(df.tail().to_markdown(index=False))
        f.write("\n\n### Data Type Classification\n")
        for key, value in type_info.items():
            f.write(f"- {key}: {value}\n")

        f.write("\n## Task 2: EDA\n")
        f.write(f"- Plots are consolidated into PDF: `{os.path.basename(plots_pdf_path)}`\n")
        f.write("\n### Correlation Matrix\n")
        f.write(corr_df.to_markdown())

        f.write("\n\n## Task 3: Missing Data and Outliers\n")
        f.write("### Missing Values\n")
        f.write(missing_before.to_markdown())
        f.write("\n\n### Outlier Counts (IQR Method)\n")
        for col, count in outliers.items():
            f.write(f"- {col}: {count}\n")
        f.write("\nImpact of outliers: extreme values can pull mean/regression slope and reduce model generalization.\n")

        f.write("\n## Task 4: Spread of Data\n")
        f.write(spread_df.to_markdown(index=False))

        f.write("\n\n## Task 5: Automated EDA\n")
        f.write("### describe()\n")
        f.write(eda_obj["describe"].to_markdown())
        f.write("\n\n### info()\n\n```")
        f.write(eda_obj["info"])
        f.write("```\n")
        f.write("\n### isnull()\n")
        f.write(eda_obj["isnull"].to_markdown())
        f.write("\n\n### corr()\n")
        f.write(eda_obj["corr"].to_markdown())

        f.write("\n\n## Task 6: Regression Analysis\n")
        f.write("- Dependent variable: Sales\n")
        f.write("- Independent variables: Quantity, Price, Flow_IN\n")
        f.write("\n### Covariance\n")
        f.write(models["covariance"].to_markdown())
        f.write("\n\n### Correlation\n")
        f.write(models["correlation"].to_markdown())

        f.write("\n\n## Task 7: Supervised Learning Models\n")
        f.write("### (i) Simple Linear Regression\n")
        f.write(f"- Train: {simple_train_metrics}\n")
        f.write(f"- Validation: {simple_val_metrics}\n")
        f.write(f"- Test: {simple_test_metrics}\n")

        f.write("\n### (ii) Multi Linear Regression\n")
        f.write(f"- Train: {multi_train_metrics}\n")
        f.write(f"- Validation: {multi_val_metrics}\n")
        f.write(f"- Test: {multi_test_metrics}\n")

        f.write("\n### (iii) Logistic Regression\n")
        f.write(f"- Accuracy: {cls_acc:.4f}\n")
        f.write(f"- Confusion Matrix:\n{cls_cm}\n")

        f.write("\n## Task 9: Overfitting / Underfitting\n")
        if not overfit_df.empty:
            f.write(overfit_df.to_markdown(index=False))
            f.write("\n\nAs degree increases, train error may reduce while test error may rise (overfitting).\n")
        else:
            f.write("Not enough data for complexity comparison.\n")

        f.write("\n## Task 10: Classification Task\n")
        f.write("- Converted target: Profit > 0 => Profitable (1), else Not Profitable (0).\n")
        f.write(f"- Accuracy: {cls_acc:.4f}\n")
        f.write(f"- Confusion Matrix:\n{cls_cm}\n")

        f.write("\n## Task 11 & 12: Model Evaluation\n")
        f.write(f"- Simple Regression Test Metrics: {simple_test_metrics}\n")
        f.write(f"- Multi Regression Test Metrics: {multi_test_metrics}\n")
        f.write(f"- Classification Accuracy: {cls_acc:.4f}\n")

        f.write("\n## Task 13: Data Visualization\n")
        f.write(f"- All plots are saved in a single PDF file: `{os.path.basename(plots_pdf_path)}`\n")
        f.write("- Temporary PNG plot files are deleted after PDF creation.\n")

    return report_path


def run_pipeline(source, start_date=None, end_date=None):
    out_dir = ensure_output_dir()
    raw_df = load_dataset(source)
    df, _, mapped = standardize_schema(raw_df)
    df, date_filter_note = apply_date_range(df, start_date=start_date, end_date=end_date)
    if df.empty:
        raise ValueError("No rows available after applying date range filter.")

    all_plot_paths = []

    type_info = classify_data_types(df)

    all_plot_paths.extend(univariate_analysis(df, out_dir))
    corr_plot_files, corr_df = bivariate_analysis(df, out_dir)
    all_plot_paths.extend(corr_plot_files)
    all_plot_paths.extend(multivariate_analysis(df, out_dir))
    all_plot_paths.extend(operational_charts(df, out_dir))

    missing_before = df.isnull().sum().to_frame("missing_count")
    mean_filled, median_filled, mode_filled = handle_missing_data(df)
    _ = mean_filled, mode_filled
    model_df = median_filled.copy()

    outlier_cols = [c for c in ["Sales", "Profit", "Quantity", "Price"] if c in model_df.columns]
    outliers = detect_outliers_iqr(model_df, outlier_cols)
    for col in outlier_cols:
        plt.figure(figsize=(7, 3.5))
        sns.boxplot(x=model_df[col])
        plt.title(f"Outlier Detection - {col}")
        all_plot_paths.append(save_plot(out_dir, f"outlier_box_{col.lower()}.png"))

    plots_pdf_path = create_pdf_and_cleanup(all_plot_paths, out_dir)

    spread_df = spread_analysis(model_df)
    eda_obj = reusable_eda_functions(model_df)
    models = regression_and_models(model_df)
    overfit_df = overfit_underfit_demo(model_df)

    report_path = save_report(
        out_dir=out_dir,
        source=source,
        df=model_df,
        mapped=mapped,
        type_info=type_info,
        corr_df=corr_df,
        missing_before=missing_before,
        outliers=outliers,
        spread_df=spread_df,
        eda_obj=eda_obj,
        models=models,
        overfit_df=overfit_df,
        plots_pdf_path=plots_pdf_path,
        date_filter_note=date_filter_note,
    )

    return out_dir, report_path


def main():
    parser = argparse.ArgumentParser(description="End-to-end Data Analytics project runner (Tasks 1-13).")
    parser.add_argument(
        "--source",
        required=True,
        help="Path to CSV/Excel/SQLite file. For SQLite, it reads table: transactions",
    )
    parser.add_argument("--start-date", required=False, help="Optional start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=False, help="Optional end date (YYYY-MM-DD)")
    args = parser.parse_args()

    out_dir, report_path = run_pipeline(args.source, start_date=args.start_date, end_date=args.end_date)
    print("Pipeline complete.")
    print(f"Output folder: {out_dir}")
    print(f"Report file: {report_path}")


if __name__ == "__main__":
    main()
