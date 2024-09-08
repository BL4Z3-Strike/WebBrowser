import sys
import sqlite3
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon

def init_db():
    conn = sqlite3.connect('passwords.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(300, 300, 400, 200)
        layout = QVBoxLayout()
        
        # Proxy Ayarları
        self.proxy_label = QLabel("Proxy URL:")
        self.proxy_input = QLineEdit()
        layout.addWidget(self.proxy_label)
        layout.addWidget(self.proxy_input)
        
        self.block_ads = QCheckBox("Ad blocker active")
        layout.addWidget(self.block_ads)
        
        self.block_js = QCheckBox("Ban JavaScript")
        layout.addWidget(self.block_js)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

class PasswordManagerDialog(QDialog):
    def __init__(self, parent=None):
        super(PasswordManagerDialog, self).__init__(parent)
        self.setWindowTitle("Password Manager")
        self.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout()
        
        self.password_list = QListWidget()
        layout.addWidget(self.password_list)
        
        form_layout = QFormLayout()
        self.website_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        form_layout.addRow("Website:", self.website_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_password)
        form_layout.addWidget(self.add_button)
        
        layout.addLayout(form_layout)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_password)
        layout.addWidget(self.delete_button)
        
        self.setLayout(layout)
        self.load_passwords()

    def add_password(self):
        website = self.website_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        if website and username and password:
            conn = sqlite3.connect('passwords.db')
            c = conn.cursor()
            c.execute('INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)', (website, username, password))
            conn.commit()
            conn.close()
            self.load_passwords()
        else:
            QMessageBox.warning(self, "Error", "You need to complete form.")

    def delete_password(self):
        selected_item = self.password_list.currentItem()
        if selected_item:
            website = selected_item.text().split(' - ')[0]
            conn = sqlite3.connect('passwords.db')
            c = conn.cursor()
            c.execute('DELETE FROM passwords WHERE website = ?', (website,))
            conn.commit()
            conn.close()
            self.load_passwords()
        else:
            QMessageBox.warning(self, "Choice Error", "You need to choose a password to delete.")

    def load_passwords(self):
        self.password_list.clear()
        conn = sqlite3.connect('passwords.db')
        c = conn.cursor()
        for row in c.execute('SELECT website, username FROM passwords'):
            self.password_list.addItem(f"{row[0]} - {row[1]}")
        conn.close()

class TabBar(QTabBar):
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
       
        self.setStyleSheet("""
            QTabBar::tab {
                padding: 5px;
                min-width: 50px;
                min-height: 20px;
            }
            QTabBar::tab:selected {
                background: lightgray;
            }
            QTabBar::tab:hover {
                background: lightblue;
            }
            QTabBar::close-button {
                image: url('icons/close.png');
            }
            QTabBar::close-button:hover {
                image: url('icons/close_hover.png');
            }
        """)

    def close_tab(self, index):
        if self.count() > 1:
            self.parent().remove_tab(index)

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.tabs = QTabWidget()
        self.tabs.setTabBar(TabBar(self))
        self.setCentralWidget(self.tabs)
        
        self.add_new_tab(QUrl("http://duckduckgo.com"), "New Tab")
        
        navbar = QToolBar()
        self.addToolBar(navbar)
        
        new_tab_btn = QAction(QIcon.fromTheme("tab-new"), "New Tab", self)
        new_tab_btn.setStatusTip("Open New Tab")
        new_tab_btn.triggered.connect(self.add_new_tab)
        navbar.addAction(new_tab_btn)
        
        back_btn = QAction(QIcon.fromTheme("go-previous"), "Previous", self)
        back_btn.setStatusTip("Go Back")
        back_btn.triggered.connect(self.current_tab_back)
        navbar.addAction(back_btn)
        
        forward_btn = QAction(QIcon.fromTheme("go-next"), "Next", self)
        forward_btn.setStatusTip("Go Next")
        forward_btn.triggered.connect(self.current_tab_forward)
        navbar.addAction(forward_btn)
        
        reload_btn = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        reload_btn.setStatusTip("Refresh Page")
        reload_btn.triggered.connect(self.current_tab_reload)
        navbar.addAction(reload_btn)
        
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)
        self.tabs.currentChanged.connect(self.update_url_bar)
        
        settings_btn = QAction(QIcon.fromTheme("preferences-system"), "Setting", self)
        settings_btn.setStatusTip("Open settings")
        settings_btn.triggered.connect(self.open_settings)
        navbar.addAction(settings_btn)
        
        password_manager_btn = QAction(QIcon.fromTheme("preferences-system"), "Password Manager", self)
        password_manager_btn.setStatusTip("Password Manage")
        password_manager_btn.triggered.connect(self.open_password_manager)
        navbar.addAction(password_manager_btn)
        
        self.proxy = None
        self.block_ads = False
        self.block_js = False

        self.load_settings()

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl("http://duckduckgo.com")
        elif isinstance(qurl, str):
            qurl = QUrl(qurl)
        elif not isinstance(qurl, QUrl):
            print(f"Warning: Expected QUrl, got {type(qurl)}")
            return
        
        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl: self.update_url_bar())
        browser.titleChanged.connect(lambda title: self.tabs.setTabText(self.tabs.currentIndex(), title))
        
        browser.page().loadFinished.connect(lambda: browser.page().runJavaScript("document.body.innerText", self.process_page_content))
    
    def process_page_content(self, content):
        if self.block_js:
            print("JavaScript banned.")
        else:
            print("JavaScript working.")

    def current_tab(self):
        return self.tabs.currentWidget()
    
    def current_tab_back(self):
        self.current_tab().back()
    
    def current_tab_forward(self):
        self.current_tab().forward()
    
    def current_tab_reload(self):
        self.current_tab().reload()
    
    def navigate_to_url(self):
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.current_tab().setUrl(q)
    
    def update_url_bar(self):
        q = self.current_tab().url()
        self.url_bar.setText(q.toString())
    
    def remove_tab(self, index):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(index)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.proxy = dialog.proxy_input.text()
            self.block_ads = dialog.block_ads.isChecked()
            self.block_js = dialog.block_js.isChecked()
            self.apply_settings()

    def open_password_manager(self):
        dialog = PasswordManagerDialog(self)
        dialog.exec_()

    def load_settings(self):
        try:
            with open("settings.txt", "r") as f:
                settings = f.readlines()
                self.proxy = settings[0].strip()
                self.block_ads = settings[1].strip().lower() == "true"
                self.block_js = settings[2].strip().lower() == "true"
        except FileNotFoundError:
            self.proxy = ""
            self.block_ads = False
            self.block_js = False
        except Exception as e:
            print(f"Settings load error: {e}")

    def apply_settings(self):
        self.apply_no_script()
    
    def apply_no_script(self):
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i).page()
            if self.block_js:
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanOpenWindows, QWebEnginePage.PermissionDenied)
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanAccessClipboard, QWebEnginePage.PermissionDenied)
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanExecute, QWebEnginePage.PermissionDenied)
            else:
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanOpenWindows, QWebEnginePage.PermissionAllowed)
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanAccessClipboard, QWebEnginePage.PermissionAllowed)
                page.setFeaturePermission(QUrl(), QWebEnginePage.JavascriptCanExecute, QWebEnginePage.PermissionAllowed)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec_())
