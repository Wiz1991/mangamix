import json
import requests
import urllib.parse
import urllib
import re
import bs4
from PyQt5.QtWidgets import(QApplication,
                            QLayout,
                            QWidget,
                            QScrollArea,
                            QLabel,
                            QMainWindow,
                            QTabWidget,
                            QVBoxLayout,
                            QLineEdit,
                            QListWidget,
                            QListWidgetItem,
                            QSizePolicy,
                            QStyle,
                            QDesktopWidget,
                            QMenu,
                            QAction,
                            qApp,
                            QMenuBar,
                                    )
from PyQt5 import Qt, QtCore, QtGui
from PyQt5.Qt import QPixmap, Qt,QThreadPool,QThread,QRunnable,pyqtSignal,QObject,pyqtSlot
from PyQt5.QtGui import QFontMetrics, QActionEvent
from selenium import webdriver
import traceback,sys,time
class SearchEngine():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engineURL = 'https://www.mangaupdates.com/search.html'

    def makeSoup(self, url):
        r = requests.get(url)
        soup = bs4.BeautifulSoup(r.text, 'lxml')
        return soup

    def getForm(self, soup):
        form = soup.find(name='form', action=re.compile(r'search.html'))
        return form

    def getAction(self, form, base_url):
        action = form['action']
        abs_action = urllib.parse.urljoin(base_url, action)
        return abs_action

    def getFormData(self, form, org_code):
        data = {}
        for inp in form('input'):
            data[inp['name']] = inp['value'] or org_code

        return data

    def search(self, query):
        soup = self.makeSoup(self.engineURL)
        form = self.getForm(soup)
        action = self.getAction(form, self.engineURL)

        data = self.getFormData(form, query)

        r = requests.post(action, data=data)
        soup = bs4.BeautifulSoup(r.content, 'html.parser')

        return self.getResaults(soup)

    def getResaults(self, soup):
        searchList = soup.findAll(alt='Series Info')
        resaults = []
        for title in searchList:
            resaults.append({'title': title.text, 'url': title['href']})

        return resaults


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super(FlowLayout, self).__init__(parent)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        del self._items[:]

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self):
        if self._hspacing >= 0:
            return self._hspacing
        else:
            return self.smartSpacing(
                QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self._vspacing >= 0:
            return self._vspacing
        else:
            return self.smartSpacing(
                QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QtCore.QSize(left + right, top + bottom)
        return size

    def doLayout(self, rect, testonly):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(+left, +top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        lineheight = 0
        for item in self._items:
            widget = item.widget()
            hspace = self.horizontalSpacing()
            if hspace == -1:
                hspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            vspace = self.verticalSpacing()
            if vspace == -1:
                vspace = widget.style().layoutSpacing(
                    QSizePolicy.PushButton,
                    QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + hspace
            if nextX - hspace > effective.right() and lineheight > 0:
                x = effective.x()
                y = y + lineheight + vspace
                nextX = x + item.sizeHint().width() + hspace
                lineheight = 0
            if not testonly:
                item.setGeometry(
                    QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = nextX
            lineheight = max(lineheight, item.sizeHint().height())
        return y + lineheight - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if parent is None:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()
    def clearList(self):
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().deleteLater()

class SeriesImage(QLabel):
    def __init__(self, str, parent=None, img=''):
        super().__init__(str, parent=parent)
        self.setPixmap(QPixmap(img))
        self.setContentsMargins(5, 5, 5, 5)
        self.setScaledContents(True)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.drawRoundedRect(0, 0, self.width() - 1,
                                self.height() - 1, 5, 5)
        super(SeriesImage, self).paintEvent(event)


class SeriesTitle(QLabel):
    def __init__(self, str, parent=None, flags=Qt.WindowFlags()):
        super().__init__(str, parent=parent, flags=flags)

        self.setWindowFlag(Qt.Dialog)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setFamilies(['ubuntu', 'sans-serif'])
        font.setWeight(650)

        self.setFont(font)
        self.setToolTip(self.text())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, 130)

        painter.drawText(self.rect(), self.alignment(), elided)


class Series(QWidget):
    def __init__(self, parent=None, imgPath='', titleText=''):
        super().__init__(parent=parent)
        box = QVBoxLayout(self)
        img = SeriesImage('', self, imgPath)
        title = SeriesTitle(titleText)

        box.addWidget(img)
        box.addWidget(title)

        self.setLayout(box)
        self.setFixedHeight(250)
        self.setFixedWidth(148)
class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
class Worker(QRunnable):
    def __init__(self, fn):
        super(Worker, self).__init__()       
        self.fn = fn
        self.signals = WorkerSignals()    

    @pyqtSlot()
    def run(self):
        try:
            self.fn()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()  # Done
    
  
       
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.threadpool = QThreadPool()
        self.initUI()

        self.initList()
        self.initSearchTab()

    def initUI(self):

        self.tabWidget = QTabWidget(self)
        self.searchEngine = SearchEngine()
        self.setGeometry(0, 0, 495, 635)
        self.center()
        self.setCentralWidget(self.tabWidget)
        self.status = self.statusBar()
        self.mainMenu = self.menuBar()

        exitAct = QAction('&Exit', self)        
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        exportList = QAction('Export &List',self)
        exportList.setShortcut('Ctrl+L')
        exportList.setStatusTip('Export your manga list(backup)')

        reloadList = QAction('Reload list',self)
        reloadList.setShortcut('Ctrl+R')
        reloadList.triggered.connect(self.loadManga)


        fileMenu = self.mainMenu.addMenu('&File')
        fileMenu.addAction(exportList)
        fileMenu.addAction(reloadList)
        fileMenu.addAction(exitAct)
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.ContextMenu  and
            source is self.searchResults):
            menu = QMenu()

            infoAction = QAction('Info',self)
            infoAction.setStatusTip('Show information about this manga title')
            infoAction.triggered.connect(self.showMangaInfo)

            addMangaAction = QAction('Add to list',self)
         
            addMangaAction.triggered.connect(self.addToList)
      
            
            menu.addAction(infoAction)
            menu.addAction(addMangaAction)
            menu.exec_(event.globalPos())
            return True
        return super(QMainWindow, self).eventFilter(source, event)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
        
    def loadManga(self):
        self.mainLayout.clearList()

        jsonObject = json.loads(open('mangalist.json').read())

        for manga in jsonObject['Manga']:
            manga = Series(self,manga['imagePath'],manga['title'])
            self.mainLayout.addWidget(manga)
        

    def initSearchTab(self):
        box = QVBoxLayout(self.tabWidget)

        widget = QWidget(self.tabWidget)

        self.inputLine = QLineEdit(widget)
        self.inputLine.returnPressed.connect(self.searchRequest)

        self.inputLine.setPlaceholderText("Search for a manga title")
        self.inputLine.setClearButtonEnabled(True)

        self.searchResults = QListWidget(widget)
        self.searchResults.setFont(QtGui.QFont('sans-serif', 10, 650))
        self.searchResults.installEventFilter(self)
        

        box.addWidget(self.inputLine)
        box.addWidget(self.searchResults)

        widget.setLayout(box)

        self.tabWidget.addTab(widget, "Search")
    
    def executeThread(self):
        self.worker = Worker(self.addToList)
        self.worker.signals.finished.connect(self.threadFinished)
        self.threadpool.start(self.worker)
    def threadFinished(self):
        
        self.loadManga()
    def addToList(self):
        url = self.searchResults.currentItem().data(QtCore.Qt.UserRole)
        self.statusBar().showMessage("Adding Manga to list.")
        driver = webdriver.PhantomJS()
        driver.get(url)
        
        soup = bs4.BeautifulSoup(driver.page_source,'lxml')

    

        title = soup.select('.tabletitle')     
        imageUrl = soup.select('.img-fluid')
        
        image  = open('images/'+title[0].text,'wb')
        image.write(requests.get(imageUrl[2]['src']).content)
        print(imageUrl[2])
        image.close()
        imagePath = 'images/'+title[0].text
        
        description = driver.find_element_by_class_name('sContent')
        
        item = {"title": "#","description":"#","imagePath":"#"}
        item["title"] =title[0].text
        item["description"]=description.text
        item["imagePath"]=imagePath

        config = json.loads(open('mangalist.json').read())

        config["Manga"].append(item)

        with open('mangalist.json','w') as f:
            f.write(json.dumps(config,indent=4))
            f.close()
    
        self.statusBar().showMessage("Manga added.",0.5)
        self.loadManga()

    def showMangaInfo(self):
        
        print(self.searchResults.currentItem().text())

    def searchRequest(self):
        resultList = self.searchEngine.search(self.inputLine.text())

        self.inputLine.clear()
        self.searchResults.clear()

        for result in resultList:
            item = QListWidgetItem(result['title'])
            item.setData(QtCore.Qt.UserRole,result['url'])

            self.searchResults.addItem(item)

    def initList(self):
        self.mainArea = QScrollArea(self)
        self.mainArea.setWidgetResizable(True)
        mangaWidget = QWidget(self.mainArea)
        self.mainLayout = FlowLayout(mangaWidget)
        self.loadManga()
        self.mainArea.setWidget(mangaWidget)
        self.tabWidget.addTab(self.mainArea, "MangaList")


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    window = MainWindow()

    window.show()
    app.exec_()
''' TODO 
    make loading from json functionality ~~DONE~~
    make refresh functionality ~~DONE~~
    add right click menu on search results ~~DONE~~
    add a dock widget for search result info, double click opens immediate
    make icon
    threaded
    DONE 
'''