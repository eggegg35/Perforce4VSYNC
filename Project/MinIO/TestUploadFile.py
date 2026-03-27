from MinIOUploader import ExecutionUpload
from MinIODownloader import ExecutionDownload

FilePath = 'D:/Temp/SyncPath.txt'
UploadExitCode = ExecutionUpload(FilePath)
print('UploadExitCode=' + str(UploadExitCode))
#
ObjectName = 'SyncPath.txt'
OutputPath = 'D:/Temp/DownloadSyncPath.txt'
DownloadExitCode = ExecutionDownload(ObjectName, OutputPath)
print('DownloadExitCode=' + str(DownloadExitCode))
