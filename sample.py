import streamlit as st
import numpy as np
import re
import pandas as pd
import assignment
import streamlit.components.v1 as components

# ページの設定
st.set_page_config(layout="wide")

class MatrixDimensionError(Exception):
    """行と列の複製係数の和が一致しない場合に発生する例外"""
    pass

def split_text_to_array(input_text):
    """
    入力テキストをタブ、スペース、改行で分割し、配列に変換する。
    """
    return re.split(r'[\t|\s|\r\n|\r|\n]', input_text)

def parse_input_matrix(input_text):
    # 入力されたテキストを行列に変換
    lines = re.split(r'\r\n|\r|\n', input_text)
    matrix = [re.split(r'\s', line) for line in lines]
    return matrix

def calculate_priority_ranking(values):
    # 値の合計を計算
    sums = np.sum(values, axis=0)
    # ランキングを計算
    ranks = pd.Series(sums).rank(method='min', ascending=False).astype(int)
    return ranks.tolist()

def create_square_matrix(numeric_matrix, row_duplication_factors, col_duplication_factors):
    # 行複製係数の和と列複製係数の和が一致するかを検証
    if sum(row_duplication_factors) != sum(col_duplication_factors):
        raise MatrixDimensionError()

    # 行を複製
    expanded_rows = [row for row, factor in zip(numeric_matrix, row_duplication_factors) for _ in range(factor)]

    # 列を複製
    expanded_matrix = [[value for value, factor in zip(row, col_duplication_factors) for _ in range(factor)] for row in expanded_rows]

    return expanded_matrix

def expand_names_and_priorities(names_text, priorities, replication_factors):
    # 行または列の複製
    names = split_text_to_array(names_text)
    expanded_names = []
    expanded_priorities = []
    for i, (priority, factor) in enumerate(zip(priorities, replication_factors)):
        if i < len(names):
            name = names[i]
        else:
            name = ""
        if factor == 1:
            expanded_names.append(name)
        else:
            expanded_names.extend([f"{name}{j+1}" for j in range(factor)])
        expanded_priorities.extend([priority] * factor)
    return expanded_names, expanded_priorities

def main():
    st.title("割当計算機")

    # 列名の入力用テキストエリア
    column_names_text = st.text_area("タブorスペースor改行区切りで各列の列名を貼り付けてください(任意)", height=68)
    
    # 行名の入力用のテキストエリア
    row_names_text = st.text_area("タブorスペースor改行区切りで各行の行名を貼り付けてください(任意)", height=68)
   
    # テキストエリアでデータを入力
    input_text = st.text_area("TVS形式の行列を貼り付けてください")
        
    # エラーメッセージ
    error_message = ""

    if input_text:
        # 入力をパースして行列に変換
        matrix = parse_input_matrix(input_text)
        
        # 行列の行数と列数を取得
        rows = len(matrix)
        cols = max(len(row) for row in matrix)

        try:
            # 空文字列を0に変換して数値に変換
            numeric_matrix = np.array([[cell if cell != '' else 0 for cell in row] for row in matrix], dtype=int)

            # 列優先順位を計算
            column_priorities = calculate_priority_ranking(numeric_matrix)

            # 行優先順位を計算
            row_priorities = calculate_priority_ranking(numeric_matrix.T)

        except ValueError as e:
            # 数値に変換できない場合や他のエラーの場合はエラーメッセージを設定
            error_message = "長方形の整数のみの行列を入力してください (空は0に変換するので許容)"
            column_priorities = [''] * cols
            row_priorities = [''] * rows

        # 行複製係数と列複製係数を追加
        row_replication_factors = ['1'] * rows
        column_replication_factors = ['1'] * cols

        # 新しい行列を作成
        new_matrix = [[''] * (cols + 2) for _ in range(rows + 2)]

        # 元の行列を中央に配置
        for i in range(rows):
            for j in range(len(matrix[i])):
                #new_matrix[i + 1][j + 1] = numeric_matrix[i][j]
                new_matrix[i + 1][j + 1] = matrix[i][j]

        # 行複製係数を左に追加
        for i in range(rows):
            new_matrix[i + 1][0] = row_replication_factors[i]

        # 列複製係数を上に追加
        for j in range(cols):
            new_matrix[0][j + 1] = column_replication_factors[j]

        # 行優先順位を右に追加
        for i in range(rows):
            new_matrix[i + 1][cols + 1] = str(row_priorities[i])

        # 列優先順位を下に追加
        for j in range(cols):
            new_matrix[rows + 1][j + 1] = str(column_priorities[j])

        # 1列目と1行目のラベルを「複」に設定
        new_matrix[0][0] = '複↓→'

        # 最終列と最終行のラベルを「優」に設定
        new_matrix[rows + 1][cols + 1] = '←↑優'

        df = pd.DataFrame(new_matrix)
        
        row_height = 20
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=False,
            height=row_height * (rows + 2) + 57,
            width=None,
            row_height=20
        )

        if st.button("割当", use_container_width=True):

            # new_matrixをdfから設定
            new_matrix = edited_df.values.tolist()
            rows = len(new_matrix) - 2
            cols = max(len(row) for row in new_matrix) - 2

            try:
                # 行列の取得
                numeric_matrix = [
                    [int(new_matrix[i + 1][j + 1]) if new_matrix[i + 1][j + 1] != '' else 0 for j in range(cols)]
                    for i in range(rows)
                ]

                # 行複製係数
                row_replication_factors = [int(new_matrix[i + 1][0]) for i in range(rows)]

                # 列複製係数
                column_replication_factors = [int(new_matrix[0][j + 1]) for j in range(cols)]

                # 行優先順位
                row_priorities = [int(new_matrix[i + 1][cols + 1]) for i in range(rows)]

                # 列優先順位
                column_priorities = [int(new_matrix[rows + 1][j + 1]) for j in range(cols)]

                # 行優先なら0、列優先なら1
                priority_flg = 1

                # 行列の種類(0ならコスト行列、1なら利益行列)
                matrix_type = 1

                # square_matrixを作成
                square_matrix = create_square_matrix(numeric_matrix, row_replication_factors, column_replication_factors)
                assignment_matrix, total_assignment = assignment.assign(square_matrix, row_priorities, column_priorities, priority_flg, matrix_type)

                # 割当結果の行列の辺のセル数
                one_side = len(assignment_matrix)

                # 新しい行列を作成
                edited_assignment_matrix = [[''] * (one_side + 2) for _ in range(one_side + 2)]

                # 元の行列を中央に配置
                for i in range(one_side):
                    for j in range(one_side):
                        edited_assignment_matrix[i + 1][j + 1] = assignment_matrix[i][j]

                # 行名と行優先順位を複製して配列に格納
                expanded_row_names, expanded_row_priorities = expand_names_and_priorities(row_names_text, row_priorities, row_replication_factors)

                # 列名と列優先順位を複製して配列に格納
                expanded_column_names, expanded_column_priorities = expand_names_and_priorities(column_names_text, column_priorities, column_replication_factors)

                # 行名を左に追加
                for i, row_name in enumerate(expanded_row_names):
                    edited_assignment_matrix[i + 1][0] = row_name

                # 行優先順位を右に追加
                for i, priority in enumerate(expanded_row_priorities):
                    edited_assignment_matrix[i + 1][one_side + 1] = str(priority)

                # 列名を上に追加
                for j, column_name in enumerate(expanded_column_names):
                    edited_assignment_matrix[0][j + 1] = column_name

                # 列優先順位を下に追加
                for j, priority in enumerate(expanded_column_priorities):
                    edited_assignment_matrix[one_side + 1][j + 1] = str(priority)

                # HTMLテーブルを作成
                html_table = f"""
                <div class='center-table'>
                    <div class='table-container'>
                        <table class='no-border-table'>
                """
                for i, row in enumerate(edited_assignment_matrix):
                    html_table += "<tr>"
                    for j, cell in enumerate(row):
                        cell_style = ""
                        if i == 0 and j == 0:
                            # 左上のセルに特定のクラスを追加
                            html_table += f"<td class='top-left-cell' style='{cell_style}'>{cell}</td>"
                        elif i == 0 and j == one_side + 1:
                            # 右上のセルに特定のクラスを追加
                            html_table += f"<td class='top-right-cell' style='{cell_style}'>{cell}</td>"
                        elif i == one_side + 1 and j == one_side + 1:
                            # 右下のセルに特定のクラスを追加
                            html_table += f"<td class='bottom-right-cell' style='{cell_style}'>{cell}</td>"
                        elif i == one_side + 1 and j == 0:
                            # 左下のセルに特定のクラスを追加
                            html_table += f"<td class='bottom-left-cell' style='{cell_style}'>{cell}</td>"
                        else:
                            if i == 0:
                                # 列名を薄い青色にし、列名は縦書きで上から下に表示する
                                cell_style = "writing-mode: vertical-lr;"
                                html_table += f"<th><span style='{cell_style}'>{cell}</span></th>"
                            elif j == 0:
                                # 行名を薄い青色にする
                                html_table += f"<th><span>{cell}</span></th>"
                            elif i == one_side + 1 or j == one_side + 1:
                                # 優先順位を薄緑色にする
                                cell_style = "background-color: #ccffcc;"
                                html_table += f"<td style='{cell_style}'>{cell}</td>"
                            else:
                                # square_matrixの値をdata属性に設定
                                html_table += f"<td style='{cell_style}' data-value='{square_matrix[i-1][j-1]}' onclick='toggleCellColor(this, {i-1}, {j-1})'>{cell}</td>"
                    html_table += "</tr>"
                html_table += f"""
                        </table>
                        <div class='vertical-label'>行優先順位</div>
                    </div>
                    <div style='text-align: center; font-weight: bold; width: 100%;'>列優先順位</div>
                </div>
                <div style="display: flex; justify-content: center; text-align: center; margin-top: 20px;">
                    <div id='sum-display' style="margin-right: 10px;">割当合計: 0</div>
                    <div>最適割当合計: {total_assignment}</div>
                </div>
                <button onclick="resetAssignment()" style="display: block; margin: 10px auto;">割当リセット</button>
                """
                
                html_js = """
                <script>
                let selectedRows = new Set();
                let selectedCols = new Set();
                let sum = 0;

                function resetAssignment() {
                    sum = 0;
                    selectedRows.clear();
                    selectedCols.clear();
                    document.querySelectorAll('td').forEach(cell => {
                        if (cell.style.backgroundColor === 'orange') {
                            cell.style.backgroundColor = '';
                        }
                    });
                    document.getElementById('sum-display').innerText = '割当合計: ' + sum;
                }

                function toggleCellColor(cell, i, j) {
                    let value = parseInt(cell.getAttribute('data-value'), 10);

                    // セルの色をトグル
                    if (cell.style.backgroundColor === 'orange') {
                        if (selectedRows.has(i)) {
                            selectedRows.delete(i);
                        }
                        if (selectedCols.has(j)) {
                            selectedCols.delete(j);
                        }  
                        cell.style.backgroundColor = '';
                        sum -= value;
                    } else {
                        if (selectedRows.has(i) || selectedCols.has(j)) {
                            return;
                        }
                        selectedRows.add(i);
                        selectedCols.add(j);
                        cell.style.backgroundColor = 'orange';
                        sum += value;
                    }
                    document.getElementById('sum-display').innerText = '割当合計: ' + sum;
                }
                </script>
                """

                # CSSスタイルを定義
                cell_size = 40  # セルのサイズを40pxに設定
                html_style = f"""
                <style>
                .center-table {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-top: 20px;
                }}
                .table-container {{
                    display: flex;
                    align-items: center;
                }}
                .vertical-label {{
                    writing-mode: vertical-rl;
                    text-orientation: upright;
                    margin-left: 10px;
                    font-weight: bold;
                }}
                .no-border-table, .no-border-table tr {{
                    border: none;
                }}
                table {{
                    border-collapse: collapse;
                    table-layout: fixed;
                }}
                th {{
                    max-width: 160px;  /* 最大幅を80pxに設定 */
                    overflow: hidden;  /* 超過した部分を隠す */
                    white-space: nowrap;  /* 改行を防ぐ */
                    text-overflow: clip;  /* 超過した部分を切り取る */
                    border: 1px solid #000;
                    background-color: #d3f9f9;
                }}
                td {{
                    width: {cell_size}px;
                    height: {cell_size}px;
                    text-align: center !important;
                    overflow: hidden;
                    white-space: nowrap;
                    border: 1px solid #000;
                }}
                .priority-text {{
                    text-align: center;
                    font-weight: bold;
                }}
                .row-priority {{
                    writing-mode: horizontal-tb;
                }}
                .column-priority {{
                    writing-mode: vertical-rl;
                    text-orientation: upright;
                    height: 100px;
                }}
                /* 左上のセルのスタイルを変更 */
                .no-border-table .top-left-cell {{
                    background-color: transparent;  /* 背景色を無しにする */
                    contenteditable: false !important;
                    border-top: none;
                    border-left: none;
                }}
                /* 右上のセルのスタイルを変更 */
                .no-border-table .top-right-cell {{
                    background-color: transparent;  /* 背景色を無しにする */
                    contenteditable: false !important;
                    border-top: none;
                    border-right: none;
                }}
                /* 右下のセルのスタイルを変更 */
                .no-border-table .bottom-right-cell {{
                    background-color: transparent;  /* 背景色を無しにする */
                    contenteditable: false !important;
                    border-right: none;
                    border-bottom: none;
                }}
                /* 左下のセルのスタイルを変更 */
                .no-border-table .bottom-left-cell {{
                    background-color: transparent;  /* 背景色を無しにする */
                    contenteditable: false !important;
                    border-left: none;
                    border-bottom: none;
                }}
                </style>
                """

                # HTMLコンテンツを表示
                components.html(html_table + html_js + html_style, height=cell_size * one_side + 500)

            except ValueError:
                error_message = "長方形の整数のみの行列を入力してください (空は0に変換するので許容)"
            except MatrixDimensionError:
                error_message = "行または列の複製後に正方形行列になるようにしてください"

    # エラーメッセージを表示
    if error_message:
        st.markdown(f"<div style='color: red; text-align: center;'>{error_message}</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top: 600px;'>
        <h2>使い方</h2>
        <ul>
            <li>ハンガリアンアルゴリズムによる割当を計算します。</li>
            <li>下記の入力イメージを参考に、エクセルやスプレッドシートから行列をコピペしてください。</li>
            <li>複数係数を2以上に設定した場合は同じ行または列を直後に複製したものを計算します。</li>
            <li>現在は優先順位は計算には使用せず、メモ用に表示しています。</li>
            <li>優先順位の初期値は各行(または各列)の値の総和を順位化したものになっています。</li>
            <li>優先順位と複製係数もエクセルやスプレッドシートからコピペで上書きできます。</li>
            <li>行を誤って追加した場合は選択してバックスペースで削除できます。</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # 画像を表示
    st.image("image.png")

if __name__ == "__main__":
    main() 
