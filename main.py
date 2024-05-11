import sys
import ast
import csv
import json
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QTextEdit, QLineEdit, QHBoxLayout, QTreeWidget, QTreeWidgetItem)
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtGui import QColor, QFont

class PythonHighlighter(QsciLexerPython):
    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)
        self.setDefaultFont(QFont("Courier", 10))

class MetricsDialog(QDialog):
    def __init__(self, metrics):
        super().__init__()
        self.setWindowTitle("Code Metrics")
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.metricsText = QTextEdit()
        self.metricsText.setPlainText(metrics)
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

class ASTViewerDialog(QDialog):
    def __init__(self, ast_tree):
        super().__init__()
        self.setWindowTitle("AST Viewer")
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(["AST Structure"])
        self.populateTree(ast_tree)
        layout.addWidget(self.treeWidget)
        self.setLayout(layout)

    def populateTree(self, node, parent=None):
        item = QTreeWidgetItem([type(node).__name__])
        if parent is None:
            self.treeWidget.addTopLevelItem(item)
        else:
            parent.addChild(item)
        for child in ast.iter_child_nodes(node):
            self.populateTree(child, item)

class SymbolTableGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Symbol Table Generator')
        layout = QVBoxLayout()

        self.label = QLabel('Select a Python file to generate symbol table:')
        layout.addWidget(self.label)

        self.editor = QsciScintilla()
        self.editor.setLexer(PythonHighlighter(self.editor))
        self.editor.setUtf8(True)
        layout.addWidget(self.editor)

        self.button = QPushButton('Browse')
        self.button.clicked.connect(self.selectFile)
        layout.addWidget(self.button)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText('Search...')
        self.searchBar.textChanged.connect(self.filterSymbols)
        layout.addWidget(self.searchBar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Symbol', 'Type', 'Scope', 'Line', 'Address'])
        self.table.itemDoubleClicked.connect(self.navigateToLine)
        layout.addWidget(self.table)

        self.metrics_button = QPushButton('Calculate Metrics')
        self.metrics_button.clicked.connect(self.calculateMetrics)
        layout.addWidget(self.metrics_button)

        self.export_button = QPushButton('Export Symbol Table')
        self.export_button.clicked.connect(self.exportSymbolTable)
        layout.addWidget(self.export_button)

        self.ast_button = QPushButton('View AST')
        self.ast_button.clicked.connect(self.showAST)
        layout.addWidget(self.ast_button)

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
                self.editor.setText(content)
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
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.add_symbol(child.name, 'Function', scope, child.lineno, id(child))
                self.process_node(child, child.name)
            elif isinstance(child, ast.ClassDef):
                self.add_symbol(child.name, 'Class', scope, child.lineno, id(child))
                self.process_node(child, child.name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        self.add_symbol(target.id, 'Variable', scope, child.lineno, id(target))
            elif isinstance(child, ast.Import):
                for name in child.names:
                    self.add_symbol(name.name, 'Import', scope, child.lineno, id(name))
            elif isinstance(child, ast.ImportFrom):
                for name in child.names:
                    self.add_symbol(name.name, 'Import', f"{scope} (from {child.module})", child.lineno, id(name))
            else:
                self.process_node(child, scope)

    def add_symbol(self, name, typ, scope, line, address):
        self.symbol_table.append((name, typ, scope, line, address))

    def navigateToLine(self, item):
        line_number = int(self.table.item(item.row(), 3).text())
        self.editor.setCursorPosition(line_number - 1, 0)
        self.editor.setSelection(line_number - 1, 0, line_number - 1, len(self.editor.text(line_number)))
        self.editor.setFocus()

    def filterSymbols(self):
        filter_text = self.searchBar.text().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            self.table.setRowHidden(row, filter_text not in item.text().lower())

    def showAST(self):
        dialog = ASTViewerDialog(self.ast_tree)
        dialog.exec_()

    def calculateMetrics(self):
        metrics = {
            'Cyclomatic Complexity': self.calculateCyclomaticComplexity(),
            'Lines of Code': self.calculateLinesOfCode(),
            'Number of Functions': self.calculateNumberOfFunctions(),
            'Number of Classes': self.calculateNumberOfClasses(),
            'Number of Imports': self.calculateNumberOfImports()
        }
        metrics_info = "\n".join(f"{key}: {value}" for key, value in metrics.items())
        dialog = MetricsDialog(metrics_info)
        dialog.exec_()

    def calculateCyclomaticComplexity(self):
        complexity = 0
        for node in ast.walk(self.ast_tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.And, ast.Or)):
                complexity += 1
        return complexity + 1

    def calculateLinesOfCode(self):
        return len(self.editor.text().splitlines())

    def calculateNumberOfFunctions(self):
        return len([node for node in ast.walk(self.ast_tree) if isinstance(node, ast.FunctionDef)])

    def calculateNumberOfClasses(self):
        return len([node for node in ast.walk(self.ast_tree) if isinstance(node, ast.ClassDef)])

    def calculateNumberOfImports(self):
        return len([node for node in ast.walk(self.ast_tree) if isinstance(node, (ast.Import, ast.ImportFrom))])

    def exportSymbolTable(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilters(["CSV files (*.csv)", "JSON files (*.json)", "XML files (*.xml)"])
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith('.csv'):
                self.exportToCSV(file_path)
            elif file_path.endswith('.json'):
                self.exportToJSON(file_path)
            elif file_path.endswith('.xml'):
                self.exportToXML(file_path)

    def exportToCSV(self, file_path):
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Symbol', 'Type', 'Scope', 'Line', 'Address'])
                for row in self.symbol_table:
                    writer.writerow(row)
            QMessageBox.information(self, 'Export Successful', f'Symbol table exported to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Failed', f'Failed to export CSV: {str(e)}')

    def exportToJSON(self, file_path):
        try:
            with open(file_path, 'w') as jsonfile:
                json.dump(self.symbol_table, jsonfile, indent=4)
            QMessageBox.information(self, 'Export Successful', f'Symbol table exported to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Failed', f'Failed to export JSON: {str(e)}')

    def exportToXML(self, file_path):
        try:
            root = ET.Element("SymbolTable")
            for name, typ, scope, line, address in self.symbol_table:
                symbol_element = ET.SubElement(root, "Symbol")
                ET.SubElement(symbol_element, "Name").text = name
                ET.SubElement(symbol_element, "Type").text = typ
                ET.SubElement(symbol_element, "Scope").text = scope
                ET.SubElement(symbol_element, "Line").text = str(line)
                ET.SubElement(symbol_element, "Address").text = str(address)
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            QMessageBox.information(self, 'Export Successful', f'Symbol table exported to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Export Failed', f'Failed to export XML: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SymbolTableGenerator()
    window.show()
    sys.exit(app.exec_())
