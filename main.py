import sys
import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QFontDatabase
from PyQt5.QtCore import Qt, QByteArray, QTimer
from PyQt5.QtSvg import QSvgRenderer

# SVG图标定义
REFRESH_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
</svg>
"""

ADD_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="16"/>
    <line x1="8" y1="12" x2="16" y2="12"/>
</svg>
"""

DELETE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="15" y1="9" x2="9" y2="15"/>
    <line x1="9" y1="9" x2="15" y2="15"/>
</svg>
"""

def svg_to_pixmap(svg_str, size):
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap

class NumericLineEdit(QLineEdit):
    def __init__(self, placeholder_text='', parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)

    def focusOutEvent(self, event):
        text = self.text().replace('。', '.')
        try:
            if text:
                float(text)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效数字。")
            self.clear()
        super().focusOutEvent(event)

class LLMComparisonTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM API 价格比较器")
        self.setGeometry(100, 100, 1200, 600)
        self.exchange_rate = 1.0
        self.load_font()
        self.initUI()
        self.get_exchange_rate()

        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(__file__), 'LLM_API_Price_Comparator-3种尺寸.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def load_font(self):
        font_path = os.path.join(os.path.dirname(__file__), 'HarmonyOS_Sans_SC_Regular.ttf')
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.custom_font = QFont(font_family, 9)
            else:
                self.custom_font = QFont()
        else:
            self.custom_font = QFont()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # 设置全局字体
        QApplication.instance().setFont(self.custom_font)

        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333333;
            }
            QPushButton {
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QLineEdit, QComboBox {
                border: 1px solid #cccccc;
                padding: 3px;
                border-radius: 2px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
        """)

        # 汇率显示和刷新
        self.exchange_rate_layout = QHBoxLayout()
        self.exchange_rate_label = QLabel("当前汇率（USD/CNY）: ")
        self.refresh_rate_button = QPushButton("刷新")
        self.refresh_rate_button.setIcon(QIcon(svg_to_pixmap(REFRESH_ICON, 24)))
        self.refresh_rate_button.setToolTip("刷新汇率")
        self.refresh_rate_button.clicked.connect(self.get_exchange_rate)
        self.exchange_rate_layout.addWidget(self.exchange_rate_label)
        self.exchange_rate_layout.addWidget(self.refresh_rate_button)
        self.exchange_rate_layout.addStretch()
        self.layout.addLayout(self.exchange_rate_layout)

        # Token输入
        self.token_input_layout = QHBoxLayout()
        self.token_input = NumericLineEdit("输入Token数")
        self.token_output = NumericLineEdit("输出Token数")
        self.token_input_layout.addWidget(QLabel("输入Token数:"))
        self.token_input_layout.addWidget(self.token_input)
        self.token_input_layout.addWidget(QLabel("输出Token数:"))
        self.token_input_layout.addWidget(self.token_output)
        self.layout.addLayout(self.token_input_layout)

        # 服务商表格
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(9)
        headers = ["服务商名称", "充值金额", "充值货币", "到账余额", "输入价格", "输出价格", "不区分输入输出", "Token单位", "操作"]
        self.providers_table.setHorizontalHeaderLabels(headers)
        self.providers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.providers_table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.providers_table)

        # 添加服务商按钮
        self.add_provider_button = QPushButton()
        self.add_provider_button.setIcon(QIcon(svg_to_pixmap(ADD_ICON, 24)))
        self.add_provider_button.setToolTip("添加更多服务商")
        self.add_provider_button.clicked.connect(self.add_provider_row)
        self.add_provider_button.setFixedSize(30, 30)
        add_button_layout = QHBoxLayout()
        add_button_layout.addStretch()
        add_button_layout.addWidget(self.add_provider_button)
        add_button_layout.addStretch()
        self.layout.addLayout(add_button_layout)

        # 结果显示
        result_layout = QVBoxLayout()
        self.result_label = QLabel("费用排名（由低至高）:")
        self.result_list = QLabel("")
        self.result_list.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.result_list)
        result_layout.setSpacing(5)
        self.layout.addLayout(result_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.calculate_button = QPushButton("计算成本")
        self.calculate_button.clicked.connect(self.calculate_costs)
        button_layout.addWidget(self.calculate_button)

        self.clear_button = QPushButton("清除所有数据")
        self.clear_button.clicked.connect(self.clear_all_data)
        button_layout.addWidget(self.clear_button)
        self.layout.addLayout(button_layout)

        # GitHub链接
        self.github_link = QLabel('<a href="https://github.com/CookSleep/LLM_API_Price_Comparator" style="color: #4a90e2;">GitHub @CookSleep</a>')
        self.github_link.setOpenExternalLinks(True)
        self.github_link.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.github_link)

        self.clear_all_data()

    def add_provider_row(self):
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)
        
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
        delete_button = QPushButton()
        delete_button.setIcon(QIcon(svg_to_pixmap(DELETE_ICON, 24)))
        delete_button.setToolTip("删除此行")
        delete_button.clicked.connect(lambda: self.delete_provider_row(self.providers_table.indexAt(delete_button.pos()).row()))

        self.providers_table.setCellWidget(row, 0, provider_name)
        self.providers_table.setCellWidget(row, 1, recharge_amount)
        self.providers_table.setCellWidget(row, 2, currency_combo)
        self.providers_table.setCellWidget(row, 3, balance)
        self.providers_table.setCellWidget(row, 4, input_price)
        self.providers_table.setCellWidget(row, 5, output_price)
        self.providers_table.setCellWidget(row, 6, input_output_checkbox)
        self.providers_table.setCellWidget(row, 7, token_unit_combo)
        self.providers_table.setCellWidget(row, 8, delete_button)

    def toggle_output_price(self, state, output_price_widget):
        output_price_widget.setDisabled(state == Qt.Checked)
        output_price_widget.setStyleSheet("background-color: #f0f0f0;" if state == Qt.Checked else "")

    def delete_provider_row(self, row):
        if self.providers_table.rowCount() <= 1:
            QMessageBox.warning(self, "警告", "至少需要保留一行数据。")
            return
        self.providers_table.removeRow(row)

    def clear_all_data(self):
        self.providers_table.setRowCount(0)
        self.token_input.clear()
        self.token_output.clear()
        self.result_list.clear()
        for _ in range(2):
            self.add_provider_row()

    def get_exchange_rate(self):
        self.refresh_rate_button.setEnabled(False)
        self.refresh_rate_button.setText("刷新中...")
        
        QTimer.singleShot(100, self.fetch_exchange_rate)

    def fetch_exchange_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            data = response.json()
            self.exchange_rate = data['rates']['CNY']
            self.exchange_rate_label.setText(f"当前汇率（USD/CNY）: {self.exchange_rate:.4f}")
        except Exception as e:
            QMessageBox.warning(self, "网络错误", "无法获取汇率，请检查网络连接后重试。")
            self.exchange_rate_label.setText("当前汇率（USD/CNY）: 获取失败")
        finally:
            self.refresh_rate_button.setEnabled(True)
            self.refresh_rate_button.setText("刷新")

    def calculate_costs(self):
        results = []
        input_tokens = float(self.token_input.text() or 0)
        output_tokens = float(self.token_output.text() or 0)

        for row in range(self.providers_table.rowCount()):
            try:
                provider_name = self.providers_table.cellWidget(row, 0).text()
                recharge_amount = float(self.providers_table.cellWidget(row, 1).text())
                currency = self.providers_table.cellWidget(row, 2).currentText()
                balance = float(self.providers_table.cellWidget(row, 3).text())
                input_price = float(self.providers_table.cellWidget(row, 4).text())
                output_price = float(self.providers_table.cellWidget(row, 5).text() or input_price)
                tokens_per_unit = {'1K token': 1000, '1M token': 1000000}[self.providers_table.cellWidget(row, 7).currentText()]

                if currency == "USD":
                    recharge_amount *= self.exchange_rate

                cost_per_token_input = (recharge_amount / balance) * input_price / tokens_per_unit
                cost_per_token_output = (recharge_amount / balance) * output_price / tokens_per_unit
                total_cost_cny = cost_per_token_input * input_tokens + cost_per_token_output * output_tokens
                total_cost_usd = total_cost_cny / self.exchange_rate
                results.append((provider_name, total_cost_cny, total_cost_usd))
            except ValueError:
                QMessageBox.warning(self, "错误", f"请检查第{row + 1}行的数据输入。")
                return
            except ZeroDivisionError:
                QMessageBox.warning(self, "错误", f"第{row + 1}行的到账余额不能为零。")
                return

        results.sort(key=lambda x: x[1])
        result_text = "\n".join([f"{name}: {cny_cost:.4f} RMB / {usd_cost:.4f} USD" for name, cny_cost, usd_cost in results])
        self.result_list.setText(result_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = LLMComparisonTool()
    mainWin.show()
    sys.exit(app.exec_())
