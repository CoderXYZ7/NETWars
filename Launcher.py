import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QLineEdit, QTabWidget, 
                             QGroupBox, QScrollArea)
from PyQt5.QtCore import QProcess, Qt

class ServerTab(QWidget):
    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port = port
        self.process = None
        self.parent = parent
        
        layout = QVBoxLayout()
        
        # Server info
        info_group = QGroupBox(f"Server on Port {port}")
        info_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Not running")
        info_layout.addWidget(self.status_label)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: black; color: white;")
        
        scroll = QScrollArea()
        scroll.setWidget(self.console_output)
        scroll.setWidgetResizable(True)
        info_layout.addWidget(scroll)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        info_layout.addLayout(btn_layout)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)
    
    def start_server(self):
        if self.process is None:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.server_finished)
            
            self.process.start("python", ["NetwarsServer.py", "--port", str(self.port)])
            if self.process.waitForStarted():
                self.status_label.setText(f"Status: Running on port {self.port}")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.console_output.append(f"Server started on port {self.port}")
    
    def stop_server(self):
        if self.process:
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()
            self.process = None
            self.status_label.setText("Status: Stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.console_output.append("Server stopped")
    
    def handle_output(self):
        data = self.process.readAllStandardOutput()
        if data:
            message = data.data().decode('utf-8').strip()
            self.console_output.append(message)
    
    def handle_error(self):
        data = self.process.readAllStandardError()
        if data:
            message = data.data().decode('utf-8').strip()
            self.console_output.append(f"ERROR: {message}")
    
    def server_finished(self):
        self.status_label.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.console_output.append("Server process finished")
        self.process = None

class NetwarsLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Netwars Launcher")
        self.setGeometry(100, 100, 800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Client launch section
        client_group = QGroupBox("Client Controls")
        client_layout = QVBoxLayout()
        
        self.launch_client_btn = QPushButton("Launch Netwars Client")
        self.launch_client_btn.clicked.connect(self.launch_client)
        client_layout.addWidget(self.launch_client_btn)
        
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        # Server control section
        server_group = QGroupBox("Server Controls")
        server_layout = QVBoxLayout()
        
        # Add server controls
        add_server_layout = QHBoxLayout()
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter port number")
        add_server_layout.addWidget(QLabel("Port:"))
        add_server_layout.addWidget(self.port_input)
        
        self.add_server_btn = QPushButton("Add Server")
        self.add_server_btn.clicked.connect(self.add_server)
        add_server_layout.addWidget(self.add_server_btn)
        
        server_layout.addLayout(add_server_layout)
        
        # Server tabs
        self.server_tabs = QTabWidget()
        server_layout.addWidget(self.server_tabs)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Add 4 default server tabs
        for port in range(5555, 5559):
            self.add_server_tab(port)
    
    def add_server_tab(self, port):
        tab = ServerTab(port, self)
        self.server_tabs.addTab(tab, f"Port {port}")
    
    def add_server(self):
        port_text = self.port_input.text()
        if port_text.isdigit():
            port = int(port_text)
            if 1024 <= port <= 65535:
                self.add_server_tab(port)
                self.port_input.clear()
            else:
                self.statusBar().showMessage("Port must be between 1024 and 65535", 3000)
        else:
            self.statusBar().showMessage("Please enter a valid port number", 3000)
    
    def launch_client(self):
        try:
            subprocess.Popen(["python", "Netwars.py"])
        except Exception as e:
            self.statusBar().showMessage(f"Failed to launch client: {str(e)}", 3000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = NetwarsLauncher()
    launcher.show()
    sys.exit(app.exec_())