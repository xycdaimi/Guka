import json
import os
import pandas as pd
import traceback


class BookMark:
    # chrome data path
    hostname = os.getlogin()
    CHROME_PATH = f"C:/Users/{hostname}/AppData/Local/Google/Chrome/User Data/Default"
    EDGE_PATH = f"C:/Users/{hostname}/AppData/Local/Microsoft/Edge/User Data/Default"
    EDGE_KILL = "taskkill /f /t /im msedge.exe"
    CHROME_KILL = "taskkill /f /t /im chrome.exe"

    def __init__(self, chromePath=EDGE_PATH):
        # chromepath
        self.chromePath = chromePath
        # refresh bookmarks
        self.bookmarks = self.get_bookmarks()

    def get_folder_data(self):
        """获取收藏夹所有的文件夹内容，合并后保存"""
        df = pd.DataFrame()
        for mark_name, item in self.bookmarks["roots"].items():
            try:
                data = pd.DataFrame(item["children"])
                data["folder_name"] = item["name"]
                df = pd.concat([df, data])
            except Exception:
                traceback.print_exc()
                print(mark_name)
        return df
        # pd.concat(df).to_csv("results.csv", encoding="utf-8")

    def get_bookmarks(self):
        """update chrome data from chrome path"""
        # parse bookmarks
        assert os.path.exists(os.path.join(self.chromePath, 'Bookmarks')), \
            "can't found ‘Bookmarks’ file,or path isn't a chrome browser cache path!"
        with open(os.path.join(self.chromePath, 'Bookmarks'), encoding='utf-8') as f:
            return json.loads(f.read())


# class dataFrame_manage_class:
def flatten_dict(d, parent_key='', sep='_'):
    """递归函数，将嵌套的字典平铺为单层字典"""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def explode_dict_array(df, col_name):
    """将DataFrame中指定列的字典数组平铺成多行记录"""
    # 检查列中是否至少有一个字典
    # if not isinstance(df[col_name].iloc[0], (list, dict)):
    # raise ValueError(f"Column '{col_name}' does not contain a list of dictionaries.")

    # 初始化新的DataFrame来存储结果
    new_rows = []

    # 遍历原始DataFrame的每一行
    for index, row in df.iterrows():
        if row['type'] != 'folder':
            new_rows.append(row.to_dict())
            continue
        # 获取当前行的字典数组
        dicts_list = row[col_name]
        # 遍历字典数组
        for d in dicts_list:
            # 递归平铺字典
            flat_dict = flatten_dict(d)

            # 将平铺后的字典与当前行的其他列合并
            new_row = {col: row[col] for col in df.columns if col != col_name}
            new_row.update(flat_dict)

            # 将新行添加到结果列表中
            new_rows.append(new_row)

            # 创建新的DataFrame
    new_df = pd.DataFrame(new_rows)

    # 返回新的DataFrame，不包含原始字典列
    return new_df.drop(columns=[col for col in new_df.columns if col.startswith(col_name)])


# if __name__ == '__main__':
#     bk = BookMark()
#     bookList = bk.get_folder_data()
#     bookList = explode_dict_array(bookList, "children")
#     print(bookList)

# @
