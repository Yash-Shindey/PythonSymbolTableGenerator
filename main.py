import sys
import ast
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QTableWidget, QTableWidgetItem, QPlainTextEdit, QDialog, QTextEdit)
from PyQt5.QtGui import QTextCursor

class MetricsDialog(QDialog):
    def __init__(self, metrics):
        super().__init__()
        self.setWindowTitle("Code Metrics")
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.metricsText = QTextEdit()
        metrics_info = "\n".join(f"{key}: {value}" for key, value in metrics.items())
        self.metricsText.setPlainText(metrics_info)
        self.metricsText.setReadOnly(True)
        layout.addWidget(self.metricsText)
        self.setLayout(layout)

class DetailedInfoDialog(QDialog):
    def __init__(self, title, details):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.infoText = QTextEdit()
        self.infoText.setPlainText(details)
        self.infoText.setReadOnly(True)
        layout.addWidget(self.infoText)
        self.setLayout(layout)

class SymbolTableGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Symbol Table Generator')
        layout = QVBoxLayout()

        self.label = QLabel('Select a Python file to generate symbol table:')
        layout.addWidget(self.label)

        self.editor = QPlainTextEdit()
        layout.addWidget(self.editor)

        self.button = QPushButton('Browse')
        self.button.clicked.connect(self.selectFile)
        layout.addWidget(self.button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Symbol', 'Type', 'Scope', 'Line', 'Address'])
        self.table.itemDoubleClicked.connect(self.navigateToLine)  # Connect the double-click event
        layout.addWidget(self.table)

        self.metrics_button = QPushButton('Calculate Metrics')
        self.metrics_button.clicked.connect(self.calculateMetrics)
        layout.addWidget(self.metrics_button)

        self.setLayout(layout)

    def selectFile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Python files (*.py)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.loadFile(file_path)

    def loadFile(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                self.editor.setPlainText(content)
            self.ast_tree = ast.parse(content)
            self.generateSymbolTable()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load file: {str(e)}')

    def generateSymbolTable(self):
        self.symbol_table = []
        self.process_node(self.ast_tree)
        self.table.setRowCount(len(self.symbol_table))
        for i, (name, typ, scope, line, address) in enumerate(self.symbol_table):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(typ))
            self.table.setItem(i, 2, QTableWidgetItem(scope))
            self.table.setItem(i, 3, QTableWidgetItem(str(line)))
            self.table.setItem(i, 4, QTableWidgetItem(str(address)))

    def process_node(self, node, scope='Global'):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) or isinstance(child, ast.AsyncFunctionDef):
                line_no = child.lineno
                address = id(child)
                self.symbol_table.append((child.name, 'Function', scope, line_no, address))
            elif isinstance(child, ast.ClassDef):
                line_no = child.lineno
                address = id(child)
                self.symbol_table.append((child.name, 'Class', scope, line_no, address))
            elif isinstance(child, ast.Assign):
                line_no = child.lineno
                # Handle multiple targets in one assignment
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        address = id(target)
                        self.symbol_table.append((target.id, 'Variable', scope, line_no, address))
            self.process_node(child, scope)
   
    def navigateToLine(self, item):
        line_number = self.table.item(item.row(), 3).text()
        cursor = self.editor.textCursor()
        cursor.setPosition(0)  # Move cursor to start of the document
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, int(line_number) - 1)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        
    def showSymbolDetails(self, item):
        symbol_name = self.table.item(item.row(), 0).text()
        details = self.find_symbol_details(symbol_name)
        dialog = DetailedInfoDialog(symbol_name, details)
        dialog.exec_()

     # ... (other methods)

    def find_symbol_details(self, symbol_name):
        """
        Search for details of the symbol with the given name.
        """
        for node in ast.walk(self.ast_tree):
            if hasattr(node, 'name') and node.name == symbol_name:
                if isinstance(node, ast.FunctionDef):
                    return self.extract_function_details(node)
                elif isinstance(node, ast.ClassDef):
                    return self.extract_class_details(node)
                elif isinstance(node, ast.Assign):
                    return self.extract_assignment_details(node)
        return "Details not found."

    def extract_function_details(self, node):
        """
        Extract details from a function definition.
        """
        args = ', '.join(arg.arg for arg in node.args.args)
        return_type = ast.unparse(node.returns) if node.returns else 'None'
        return f"Function {node.name}\nArguments: {args}\nReturn Type: {return_type}"

    def extract_class_details(self, node):
        """
        Extract details from a class definition.
        """
        bases = ', '.join(ast.unparse(base) for base in node.bases)
        return f"Class {node.name}\nBases: {bases}"

    def extract_assignment_details(self, node):
        """
        Extract details from an assignment.
        """
        targets = ', '.join(ast.unparse(target) for target in node.targets)
        return f"Assigned to: {targets}"

    def calculateMetrics(self):
        """
        Calculate various code metrics.
        """
        metrics = {
            'Cyclomatic Complexity': self.calculateCyclomaticComplexity(),
            'Lines of Code': self.calculateLinesOfCode(),
            'Number of Functions': self.calculateNumberOfFunctions(),
            'Number of Classes': self.calculateNumberOfClasses(),
        }
        dialog = MetricsDialog(metrics)
        dialog.exec_()

    def calculateCyclomaticComplexity(self):
        """
        Calculate the cyclomatic complexity of the code.
        """
        complexity = 0
        for node in ast.walk(self.ast_tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.And, ast.Or)):
                complexity += 1
        return complexity + 1

    def calculateLinesOfCode(self):
        """
        Calculate the total number of lines of code.
        """
        return len(self.editor.toPlainText().splitlines())

    def calculateNumberOfFunctions(self):
        """
        Calculate the total number of function definitions.
        """
        return len([node for node in ast.walk(self.ast_tree) if isinstance(node, ast.FunctionDef)])

    def calculateNumberOfClasses(self):
        """
        Calculate the total number of class definitions.
        """
        return len([node for node in ast.walk(self.ast_tree) if isinstance(node, ast.ClassDef)])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SymbolTableGenerator()
    window.show()
    sys.exit(app.exec_())
