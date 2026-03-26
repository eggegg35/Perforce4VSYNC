using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace EditorCommon
{
    public class PyUtils
    {
        public static DirectoryInfo ProjectPath = Directory.GetParent(Application.dataPath);

        public static string LuaDataPath = Path.Combine(ProjectPath.FullName.Replace("unity_project",
            @"client\LuaScripts\Data"));
        public static async void CallPY(string cmd, string args, string filePath, Action<string> callback)
        {
            try
            {
                var errorInfo = "";
                if (string.IsNullOrEmpty(cmd))
                    errorInfo = "Error 没有指定操作行为";
                if (string.IsNullOrEmpty(filePath))
                    errorInfo = "Error 没有指定目录或者文件";
                if (string.IsNullOrEmpty(errorInfo))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo()
                    {
                        FileName = GetPythonExePath(),
                        Arguments = $"{GetP4ToolDirPath()}//PyTool.py --filePath {filePath} --cmd {cmd} --args {args}",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = GetCurEncoding(),
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process process = Process.Start(startInfo);
                    Task<string> outputTask = process.StandardOutput.ReadToEndAsync();
                    Task processTask = Task.Run(() => { process.WaitForExit(); });
                    await Task.WhenAll(outputTask, processTask);
                    Debug.Log(startInfo.Arguments);
                    Debug.Log(outputTask.Result);
                    callback?.Invoke(GetRetrunStr(outputTask.Result));
                }
            }
            catch (Exception e)
            {
                Debug.LogError(e);
                callback?.Invoke(string.Empty);
            }
        }

        public static async Task<string> CallPYAsync(string cmd, string args, string filePath)
        {
            try
            {
                var errorInfo = "";
                if (string.IsNullOrEmpty(cmd))
                    errorInfo = "Error 没有指定操作行为";
                if (string.IsNullOrEmpty(filePath))
                    errorInfo = "Error 没有指定目录或者文件";
                if (string.IsNullOrEmpty(errorInfo))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo()
                    {
                        FileName = GetPythonExePath(),
                        Arguments = $"{GetP4ToolDirPath()}//PyTool.py --filePath {filePath} --cmd {cmd} --args {args}",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = GetCurEncoding(),
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process process = Process.Start(startInfo);
                    Task<string> outputTask = process.StandardOutput.ReadToEndAsync();
                    Task processTask = Task.Run(() => { process.WaitForExit(); });
                    await Task.WhenAll(outputTask, processTask);
                    UnityEngine.Debug.Log(startInfo.Arguments);
                    UnityEngine.Debug.Log(outputTask.Result);
                    return GetRetrunStr(outputTask.Result);
                }
            }
            catch (Exception e)
            {
                Debug.LogError(e);
                return string.Empty;
            }

            return string.Empty;
        }

        public static string CallPY(string cmd, string args, string filePath)
        {
            try
            {
                var errorInfo = "";
                if (string.IsNullOrEmpty(cmd))
                    errorInfo = "Error 没有指定操作行为";
                if (string.IsNullOrEmpty(filePath))
                    errorInfo = "Error 没有指定目录或者文件";
                if (string.IsNullOrEmpty(errorInfo))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo()
                    {
                        FileName = GetPythonExePath(),
                        Arguments = $"{GetP4ToolDirPath()}//PyTool.py --filePath {filePath} --cmd {cmd} --args {args}",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true,
                        StandardOutputEncoding = GetCurEncoding(),
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process process = Process.Start(startInfo);
                    string outPut = process.StandardOutput.ReadToEnd();
                    Debug.Log(startInfo.Arguments);
                    Debug.Log(outPut);
                    return GetRetrunStr(outPut);
                }
            }
            catch (Exception e)
            {
                Debug.LogError(e);
                return string.Empty;
            }

            return string.Empty;
        }

        private static string GetRetrunStr(string input)
        {
            if (input.Contains("returnStrStart") && input.Contains("returnStrEnd"))
            {
                string start = "returnStrStart-- ";
                string end = " --returnStrEnd";

                int startIndex = input.IndexOf(start, StringComparison.Ordinal) + start.Length;
                int endIndex = input.IndexOf(end, startIndex, StringComparison.Ordinal);

                if (startIndex >= 0 && endIndex >= 0)
                {
                    string result = input[startIndex..endIndex];
                    return result;
                }

                return "";
            }

            return "";
        }
        
        private static string GetPythonExePath(string exeName = "python.exe")
        {
            
            var path = Path.Combine(ProjectPath.FullName.Replace("unity_project", "tools"), "Python37/python.exe");
            //UnityEngine.Debug.Log(path);
            if (File.Exists(path))
            {
                return path;
            }
            throw new Exception($"获取{exeName}的路径失败！请及时更新P4仓库，请更新tools目录");
        }
        
        private static string GetP4ToolDirPath()
        {
            return Application.dataPath.Replace("Assets", "Packages\\com.funplus.worldx.editor-common\\Editor\\Python");
        }
        
        [DllImport("kernel32.dll")]
        private static extern int GetACP();
        public static Encoding GetCurEncoding()
        {
            int ansiCodePage = GetACP();
            Encoding ansiEncoding = Encoding.GetEncoding(ansiCodePage);
            UnityEngine.Debug.Log($"当前系统编码：{ansiEncoding.WebName}");
            return ansiEncoding;
        }
    }
}