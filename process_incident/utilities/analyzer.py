import json
import pandas as pd

class DatasetAnalyzer:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.df = pd.DataFrame(json.load(f))

    def category_distribution(self):
        return self.df["category"].value_counts()

    def critical_by_category(self):
        return pd.crosstab(
            self.df["category"],
            self.df["critical"]
        )

    def scope_distribution(self):
        return self.df["scope"].value_counts()