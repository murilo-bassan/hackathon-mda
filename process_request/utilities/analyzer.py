import json
import pandas as pd

class DatasetAnalyzer:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.df = pd.DataFrame(json.load(f))

    def category_distribution(self):
        return self.df["category"].value_counts()

    def priority_by_category(self):
        return pd.crosstab(
            self.df["category"],
            self.df["resulting_priority"]
        )

    def department_distribution(self):
        return self.df["department"].value_counts()