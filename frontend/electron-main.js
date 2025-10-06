// 简化的Electron主进程文件
const { app, BrowserWindow } = require('electron')
const path = require('path')

console.log('Electron starting...')

function createWindow() {
  console.log('Creating window...')
  
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    show: false
  })

  // 总是加载开发URL，因为我们在开发模式
  console.log('Loading URL: http://localhost:5173')
  mainWindow.loadURL('http://localhost:5173')

  mainWindow.once('ready-to-show', () => {
    console.log('Window ready, showing...')
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    console.log('Window closed')
  })
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})