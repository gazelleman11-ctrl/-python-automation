"""
10月販売構成.xlsx を読み込み、集計結果をターミナル表示＋グラフ保存するスクリプト。
グラフ生成をスキップする場合は --no-chart オプションを付けて実行。
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

EXCEL_FILE = "10月販売構成.xlsx"

# Sequential blue ramp (dataviz palette, step 200→600, light→dark)
BLUE_RAMP = ["#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf",
             "#1c5cab", "#184f95", "#104281"]


def load_data(path: str) -> tuple[pd.DataFrame, str, str, str]:
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]
    col_name, col_count, col_amount = df.columns[0], df.columns[1], df.columns[2]
    # 集計行を除外（合計・総計など「計」を含む行を除去）
    df = df[~df[col_name].astype(str).str.contains("計", na=False)].reset_index(drop=True)
    return df, col_name, col_count, col_amount


def print_summary(df: pd.DataFrame, col_name: str, col_count: str, col_amount: str) -> None:
    total_count  = df[col_count].sum()
    total_amount = df[col_amount].sum()

    sep = "─" * 68
    print(f"\n{'─'*68}")
    print(f"  10月 販売構成サマリー")
    print(sep)
    print(f"  {'商品名':<20}  {'数量':>6}  {'構成比':>6}  {'金額(円)':>12}  {'金額比':>6}")
    print(sep)

    for _, row in df.sort_values(col_amount, ascending=False).iterrows():
        pct_cnt = row[col_count]  / total_count  * 100
        pct_amt = row[col_amount] / total_amount * 100
        print(
            f"  {row[col_name]:<20}  "
            f"{row[col_count]:>6,}  "
            f"{pct_cnt:>5.1f}%  "
            f"{row[col_amount]:>12,}  "
            f"{pct_amt:>5.1f}%"
        )

    print(sep)
    print(
        f"  {'合計':<20}  "
        f"{total_count:>6,}  "
        f"{'100.0%':>6}  "
        f"{total_amount:>12,}  "
        f"{'100.0%':>6}"
    )
    print(f"{'─'*68}\n")


def make_charts(df: pd.DataFrame, col_name: str, col_count: str, col_amount: str, out_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    # 日本語フォントを探す（なければデフォルト）
    jp_fonts = [f.name for f in fm.fontManager.ttflist
                if any(k in f.name for k in ("Gothic", "Meiryo", "Yu", "Noto"))]
    font = jp_fonts[0] if jp_fonts else None
    if font:
        plt.rcParams["font.family"] = font

    surface = "#fcfcfb"
    text_primary   = "#0b0b0b"
    text_secondary = "#52514e"
    gridline       = "#e1e0d9"
    baseline       = "#c3c2b7"

    def _horizontal_bar(series: pd.Series, title: str, xlabel: str,
                        fmt_fn, filename: str) -> None:
        s = series.sort_values()          # 昇順 → 上が大きい
        n = len(s)
        colors = BLUE_RAMP[-n:]           # 値が大きいほど濃い青

        fig, ax = plt.subplots(figsize=(9, 4.8))
        fig.patch.set_facecolor(surface)
        ax.set_facecolor(surface)

        bars = ax.barh(s.index, s.values, color=colors,
                       height=0.55, linewidth=0)

        # 直接ラベル
        for bar, val in zip(bars, s.values):
            ax.text(val + s.max() * 0.012, bar.get_y() + bar.get_height() / 2,
                    fmt_fn(val), va="center", fontsize=9, color=text_primary)

        # 軸・グリッド
        ax.set_xlabel(xlabel, fontsize=9, color=text_secondary)
        ax.set_title(title, fontsize=13, fontweight="bold",
                     color=text_primary, pad=14)
        ax.tick_params(colors=text_secondary, labelsize=9)
        ax.xaxis.set_tick_params(color=baseline)
        ax.yaxis.set_tick_params(color=baseline)
        ax.spines[:].set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(baseline)
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, color=gridline, linewidth=0.6)
        ax.set_xlim(0, s.max() * 1.18)

        plt.tight_layout()
        path = out_dir / filename
        fig.savefig(path, dpi=150, facecolor=surface)
        plt.close(fig)
        print(f"  グラフを保存しました: {path}")

    df_sorted = df.set_index(col_name)

    _horizontal_bar(
        df_sorted[col_count],
        title="10月 商品別 販売数量",
        xlabel="販売合計数（個）",
        fmt_fn=lambda v: f"{int(v):,}",
        filename="sales_count_oct.png",
    )

    _horizontal_bar(
        df_sorted[col_amount],
        title="10月 商品別 販売金額",
        xlabel="販売合計金額（円）",
        fmt_fn=lambda v: f"¥{int(v):,}",
        filename="sales_amount_oct.png",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="10月販売構成 集計・グラフ化")
    parser.add_argument("--no-chart", action="store_true",
                        help="ターミナル表示のみ（グラフ非生成）")
    args = parser.parse_args()

    excel_path = Path(EXCEL_FILE)
    if not excel_path.exists():
        print(f"[ERROR] ファイルが見つかりません: {excel_path}", file=sys.stderr)
        sys.exit(1)

    df, col_name, col_count, col_amount = load_data(str(excel_path))
    print_summary(df, col_name, col_count, col_amount)

    if not args.no_chart:
        print("グラフを生成しています...")
        make_charts(df, col_name, col_count, col_amount, out_dir=Path("."))
        print("完了")


if __name__ == "__main__":
    main()
