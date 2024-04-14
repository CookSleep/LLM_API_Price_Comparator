import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QMessageBox, QGridLayout,
    QScrollArea, QFrame
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

def validate_float(text):
    try:
        if text:
            text = text.replace('。', '.')
            float(text)
            return True
        return False
    except ValueError:
        return False

class NumericLineEdit(QLineEdit):
    def __init__(self, placeholder_text='', parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)

    def focusOutEvent(self, event):
        text = self.text()
        if text and not validate_float(text):
            QMessageBox.warning(self, "输入错误", "请输入有效数字。")
            self.clear()
        super().focusOutEvent(event)

class LLMComparisonTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM API价格比较器")
        self.setWindowIcon(QIcon("D:\\Price\\LLM API Price Comperator.ico"))
        self.setGeometry(100, 100, 1200, 350)
        self.exchange_rate = 1.0
        self.initUI()
        self.get_exchange_rate()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.exchange_rate_layout = QHBoxLayout()
        self.exchange_rate_label = QLabel("当前汇率（USD/CNY）: 获取中...")
        self.refresh_rate_button = QPushButton("刷新汇率")
        self.refresh_rate_button.clicked.connect(self.get_exchange_rate)
        self.exchange_rate_layout.addWidget(self.exchange_rate_label)
        self.exchange_rate_layout.addWidget(self.refresh_rate_button)
        self.layout.addLayout(self.exchange_rate_layout)

        self.token_input_layout = QHBoxLayout()
        self.token_input = NumericLineEdit("输入Token数")
        self.token_output = NumericLineEdit("输出Token数")
        self.token_input_layout.addWidget(QLabel("输入Token数:"))
        self.token_input_layout.addWidget(self.token_input)
        self.token_input_layout.addWidget(QLabel("输出Token数:"))
        self.token_input_layout.addWidget(self.token_output)
        self.layout.addLayout(self.token_input_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_frame = QFrame()
        self.scroll_area.setWidget(self.scroll_frame)
        self.layout.addWidget(self.scroll_area)

        self.providers_grid = QGridLayout(self.scroll_frame)
        headers = ["服务商名称", "充值金额 (仅数字)", "充值货币", "到账余额 (仅数字)", "输入价格 (仅数字)", "输出价格 (仅数字)", "不区分输入输出", "Token单位", "操作"]
        for i, header in enumerate(headers):
            self.providers_grid.addWidget(QLabel(header), 0, i)

        self.add_provider_button = QPushButton("添加更多服务商")
        self.add_provider_button.clicked.connect(self.add_provider_row)
        self.layout.addWidget(self.add_provider_button)

        self.result_label = QLabel("费用排名（由低至高）:")
        self.result_list = QLabel("")
        self.layout.addWidget(self.result_label)
        self.layout.addWidget(self.result_list)

        self.calculate_button = QPushButton("计算成本")
        self.calculate_button.clicked.connect(self.calculate_costs)
        self.layout.addWidget(self.calculate_button)

        self.clear_button = QPushButton("清除所有数据")
        self.clear_button.clicked.connect(self.clear_all_data)
        self.layout.addWidget(self.clear_button)

        self.github_link = QLabel('<a href="https://github.com/CookSleep/LLM-API-Price-Comperator">GitHub @CookSleep</a>')
        self.github_link.setOpenExternalLinks(True)
        self.github_link.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.github_link)

        self.clear_all_data()

    def add_provider_row(self):
        index = self.providers_grid.rowCount()
        provider_name = QLineEdit()
        recharge_amount = NumericLineEdit("仅数字")
        currency_combo = QComboBox()
        currency_combo.addItems(["CNY", "USD"])
        balance = NumericLineEdit("仅数字")
        input_price = NumericLineEdit("仅数字")
        output_price = NumericLineEdit("仅数字")
        input_output_checkbox = QCheckBox()
        input_output_checkbox.stateChanged.connect(lambda state, x=output_price: self.toggle_output_price(state, x))
        token_unit_combo = QComboBox()
        token_unit_combo.addItems(["1K token", "1M token"])
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(lambda: self.delete_provider_row(index))

        row_widgets = [provider_name, recharge_amount, currency_combo, balance, input_price, output_price, input_output_checkbox, token_unit_combo, delete_button]
        for i, widget in enumerate(row_widgets):
            self.providers_grid.addWidget(widget, index, i)

    def toggle_output_price(self, state, output_price_widget):
        if state == Qt.Checked:
            output_price_widget.setDisabled(True)
        else:
            output_price_widget.setDisabled(False)

    def delete_provider_row(self, index):
        for j in range(9):
            item = self.providers_grid.itemAtPosition(index, j)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def clear_all_data(self):
        for i in reversed(range(1, self.providers_grid.rowCount())):
            self.delete_provider_row(i)
        self.token_input.clear()
        self.token_output.clear()
        for _ in range(2):
            self.add_provider_row()

    def get_exchange_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            data = response.json()
            self.exchange_rate = data['rates']['CNY']
            self.exchange_rate_label.setText(f"当前汇率（USD/CNY）: {self.exchange_rate:.4f}")
        except Exception as e:
            QMessageBox.warning(self, "网络错误", "无法获取汇率，请检查网络连接后重试。")
            self.exchange_rate_label.setText("当前汇率（USD/CNY）: 获取失败")

    def calculate_costs(self):
        results = []
        input_tokens = float(self.token_input.text()) if self.token_input.text() else 0
        output_tokens = float(self.token_output.text()) if self.token_output.text() else 0

        for i in range(1, self.providers_grid.rowCount()):
            try:
                provider_name = self.providers_grid.itemAtPosition(i, 0).widget().text()
                recharge_amount = float(self.providers_grid.itemAtPosition(i, 1).widget().text())
                currency = self.providers_grid.itemAtPosition(i, 2).widget().currentText()
                balance = float(self.providers_grid.itemAtPosition(i, 3).widget().text())
                input_price = float(self.providers_grid.itemAtPosition(i, 4).widget().text())
                output_price = float(self.providers_grid.itemAtPosition(i, 5).widget().text()) if self.providers_grid.itemAtPosition(i, 6).widget().checkState() == Qt.Unchecked else input_price
                tokens_per_unit = {'1K token': 1000, '1M token': 1000000}[self.providers_grid.itemAtPosition(i, 7).widget().currentText()]

                if currency == "USD":
                    recharge_amount *= self.exchange_rate

                cost_per_token_input = (recharge_amount / balance) * input_price / tokens_per_unit
                cost_per_token_output = (recharge_amount / balance) * output_price / tokens_per_unit
                total_cost_cny = cost_per_token_input * input_tokens + cost_per_token_output * output_tokens
                total_cost_usd = total_cost_cny / self.exchange_rate
                results.append((provider_name, total_cost_cny, total_cost_usd))
            except ValueError:
                QMessageBox.warning(self, "错误", f"请检查第{i}行的数据输入。")
                return

        results.sort(key=lambda x: x[1])
        result_text = "\n".join([f"{name}: {cny_cost:.4f} RMB / {usd_cost:.4f} USD" for name, cny_cost, usd_cost in results])
        self.result_list.setText(result_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = LLMComparisonTool()
    mainWin.show()
    sys.exit(app.exec_())
