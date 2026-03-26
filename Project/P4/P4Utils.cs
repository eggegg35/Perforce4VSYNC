using LuaInterface;
using Sirenix.OdinInspector;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using EditorCommon.Editor;
using UnityEditor;
using UnityEngine;
using LitJson;
using Newtonsoft.Json.Linq;
using Sirenix.Utilities;
using Sirenix.Utilities.Editor;
using Debug = System.Diagnostics.Debug;

namespace EditorCommon
{
    
    public class InputP4ConfigPopupWizard : ScriptableWizard
    {
        private static InputP4ConfigPopupWizard Instance = null;
        private static bool show = false;

        private static string P4_INFO_RECORD_PATH => Application.dataPath.Replace("Assets", $"LocalP4Setting.json");

        private static string p4UserName;
        private static string workspace;
        private static string realName;
        private static bool isAutoLoaded = false;

        [MenuItem("Window/P4/设置P4信息")]
        public static void Open()
        {
            Show();
        }
        
        /// <summary>
        /// 从P4命令自动获取配置信息
        /// </summary>
        private static void AutoLoadP4Info()
        {
            try
            {
                string unityProjectPath = System.IO.Path.GetDirectoryName(Application.dataPath);
                string infoOutput = RunP4Command("info", unityProjectPath);
                
                // 解析 User name
                var userMatch = Regex.Match(infoOutput, @"User name:\s*(\S+)");
                if (userMatch.Success)
                {
                    p4UserName = userMatch.Groups[1].Value;
                }
                
                // 解析 Client name
                var clientMatch = Regex.Match(infoOutput, @"Client name:\s*(\S+)");
                if (clientMatch.Success)
                {
                    workspace = clientMatch.Groups[1].Value;
                }
                
                isAutoLoaded = true;
                UnityEngine.Debug.Log($"[P4] 自动加载P4信息成功: User={p4UserName}, Client={workspace}");
            }
            catch (System.Exception ex)
            {
                UnityEngine.Debug.LogWarning($"[P4] 自动加载P4信息失败: {ex.Message}");
            }
        }
        
        private static string RunP4Command(string arguments, string workingDirectory)
        {
            var process = new System.Diagnostics.Process
            {
                StartInfo = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "p4",
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.Default,
                    StandardErrorEncoding = Encoding.Default,
                    WorkingDirectory = workingDirectory
                }
            };
            
            process.Start();
            string output = process.StandardOutput.ReadToEnd();
            process.WaitForExit();
            return output;
        }

        public static bool CheckP4Info(bool ShowWnd = true)
        {
            string p4UserName = null;
            string workspace = null;
            string userName = null;
            if (File.Exists(P4_INFO_RECORD_PATH))
            {
                var jsonData = JsonMapper.ToObject(File.ReadAllText(P4_INFO_RECORD_PATH));
                p4UserName = jsonData["P4_UserName"].ToString();
                workspace = jsonData["P4_WorkSpace"].ToString();
                userName = jsonData["RealUserName"].ToString();
            }
            else
            {
                p4UserName = EditorPrefs.GetString("P4_UserName", "");
                workspace = EditorPrefs.GetString("P4_WorkSpace", "");
                userName = EditorPrefs.GetString("RealUserName", "");
                var jsonData = new JsonData();
                jsonData["P4_UserName"] = p4UserName;
                jsonData["P4_WorkSpace"] = workspace;
                jsonData["RealUserName"] = userName;
                if (!File.Exists(P4_INFO_RECORD_PATH))
                {
                    File.Create(P4_INFO_RECORD_PATH).Dispose();
                }
                File.WriteAllText(P4_INFO_RECORD_PATH, JsonMapper.ToJson(jsonData));
            }
            if (string.IsNullOrEmpty(p4UserName) || string.IsNullOrEmpty(workspace) || string.IsNullOrEmpty(userName))
            {
                if (ShowWnd)
                {
                    if (EditorUtility.DisplayDialog("提示", "请先完善一下P4相关信息再操作!",
                            "好的"))
                    {
                        Open();
                    }
                }
                else
                {
                    UnityEngine.Debug.LogWarning("请先完善一下P4相关信息再操作!");
                }
                return false;
            }

            return true;
        }


        public static string GetName()
        {
            if (File.Exists(P4_INFO_RECORD_PATH))
            {
                var jsonData = JsonMapper.ToObject(File.ReadAllText(P4_INFO_RECORD_PATH));
                return jsonData["P4_UserName"].ToString();
            }
            else
            {
                return EditorPrefs.GetString("P4_UserName", "");
            }
        }
        
        public static string GetWorkspace()
        {
            if (File.Exists(P4_INFO_RECORD_PATH))
            {
                var jsonData = JsonMapper.ToObject(File.ReadAllText(P4_INFO_RECORD_PATH));
                return jsonData["P4_WorkSpace"].ToString();
            }
            else
            {
                return EditorPrefs.GetString("P4_WorkSpace", "");
            }
        }
        
        private static bool loadRealNameFlag = false;
        public static string GetRealName()
        {
            if (!loadRealNameFlag)
            {
                if (File.Exists(P4_INFO_RECORD_PATH))
                {
                    var jsonData = JsonMapper.ToObject(File.ReadAllText(P4_INFO_RECORD_PATH));
                    realName = jsonData["RealUserName"].ToString();
                }
                else
                {
                    realName = EditorPrefs.GetString("RealUserName", "");
                }

                loadRealNameFlag = true;
            }
            return realName;
        }
        
        public static void Show(string title = "输入P4信息")
        {
            var window = show
                ? Instance
                : ScriptableWizard.DisplayWizard<InputP4ConfigPopupWizard>(title) as InputP4ConfigPopupWizard;

            if (File.Exists(P4_INFO_RECORD_PATH))
            {
                var jsonData = JsonMapper.ToObject(File.ReadAllText(P4_INFO_RECORD_PATH));
                p4UserName = jsonData["P4_UserName"].ToString();
                workspace = jsonData["P4_WorkSpace"].ToString();
                realName = jsonData["RealUserName"].ToString();
            }
            else
            {
                p4UserName = EditorPrefs.GetString("P4_UserName", "");
                workspace = EditorPrefs.GetString("P4_WorkSpace", "");
                realName = EditorPrefs.GetString("RealUserName", "");
            }
            window.maxSize = new Vector2(400, 200);
            window.minSize = new Vector2(400, 180);
        }

        private void OnEnable()
        {
            show = true;
            Instance = this;
        }

        public void OnDisable()
        {
            show = false;
            Instance = null;
        }

        private void OnGUI()
        {
            EditorGUILayout.BeginVertical();
            
            // 工具栏
            EditorGUILayout.BeginHorizontal(EditorStyles.toolbar);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("自动获取", EditorStyles.toolbarButton, GUILayout.Width(70)))
            {
                AutoLoadP4Info();
                Repaint();
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.Space(5);
            
            // 输入字段
            p4UserName = EditorGUILayout.TextField("P4UserName", p4UserName);
            workspace = EditorGUILayout.TextField("P4Workspace", workspace);
            realName = EditorGUILayout.TextField("真实姓名", realName);
            
            EditorGUILayout.Space(5);
            
            // 提示信息
            if (isAutoLoaded)
            {
                EditorGUILayout.HelpBox("✓ 已自动获取P4信息，请确认后保存", MessageType.Info);
            }
            
            EditorGUILayout.Space(5);
            
            // 按钮
            using (new GUILayout.HorizontalScope())
            {
                if (GUILayout.Button("保存"))
                {
                    var jsonData = new JsonData();
                    jsonData["P4_UserName"] = p4UserName;
                    jsonData["P4_WorkSpace"] = workspace;
                    jsonData["RealUserName"] = realName;
                    if (!File.Exists(P4_INFO_RECORD_PATH))
                    {
                        File.Create(P4_INFO_RECORD_PATH).Dispose();
                    }
                    File.WriteAllText(P4_INFO_RECORD_PATH, JsonMapper.ToJson(jsonData));
                    isAutoLoaded = false;
                    UnityEngine.Debug.Log("[P4] P4配置信息已保存");
                    Close();
                }

                if (GUILayout.Button("关闭"))
                {
                    isAutoLoaded = false;
                    Close();
                }
            }
            
            EditorGUILayout.EndVertical();
        }
    }
    
    public struct UpdateFailFile
    {
        public string reason;
        public string file;
    }

    public class ChangeListInfo
    {
        public string changeId;
        public string desc;
    }

    [Serializable]
    public class ChangeFileInfo
    {
        public string depotFile;
        public string clientFile;
        public string workRev;
        public string action;
        public string type;

        //扩展信息
        public string ext = "";

        public bool select { get; set; }
    }

    public class LatestInfo
    {
        public string time;
        public string client;
        public string desc;
        public string change;
        public string user;
    }

    public enum LockType
    {
        NoLock,
        LockBySelf,
        LockByOther
    }
    public class FstatFileInfo
    {
        public LockType lockType;
        public string clientFile;
        public string lockerName;
        public string headAction;
    }

    /// <summary>
    /// 封装C#直接调用P4。Provider有限制只能操作Assets下的文件。
    /// 命令行调用P4命令。注意这里是异步调用，回调的第一个bool参数表示本次调用成功。
    /// </summary>
    public class P4Utils
    {
        private static string _workSpace;
        public static string WorkSpace
        {
            get
            {
                var currentWorkspace= InputP4ConfigPopupWizard.GetWorkspace();
                if (_workSpace != currentWorkspace)
                {
                    _workSpace = currentWorkspace;
                    UnityEngine.Debug.Log($"检测到workSpace更改！！已切换至{_workSpace}");
                }
                if (string.IsNullOrEmpty(_workSpace))
                {
                    UnityEngine.Debug.LogError("获取WorkSpace失败！！");
                    return "";
                }
                return _workSpace;
            }
        }

        private static string _userName;
        public static string UserName
        {
            get
            {
                var currentName = InputP4ConfigPopupWizard.GetName();
                if (_userName != currentName)
                {
                    _userName = currentName;
                    UnityEngine.Debug.Log($"检测到username更改！！已切换至{_userName}");
                }
                if (string.IsNullOrEmpty(_userName))
                {
                    UnityEngine.Debug.LogError("获取userName失败！！");
                    return "";
                }
                return _userName;
            }
        }

        public static void Revert(string dir, Action<bool, string> callback)
        {
            CallP4("revert", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, dir, "");
        }
        
        public static void DeleteFileList(string dir, Action<bool, string> callback)
        {
            CallP4("revert", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, dir, "");
        }
        public static void Update(string dir, Action<bool, List<UpdateFailFile>> callback,bool async = true)
        {
            Action<string> callAction_ = (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var updateFailFiles = new List<UpdateFailFile>();
                    var strs = result.Split('|');
                    foreach (var s in strs)
                    {
                        if (string.IsNullOrEmpty(s) || s.Contains("up-to-date") || s.Contains("no such file")) continue;
                        var info = s.TrimStart().TrimEnd();
                        if (string.IsNullOrEmpty(info) || !info.Contains(" - ")) continue;
                        var infos = info.Split(" - ")[1];
                        var reason = infos.Split(" file ")[0];
                        var file = infos.Split(" file ")[1];
                        updateFailFiles.Add(new UpdateFailFile() { reason = reason, file = file });
                    }
                    callback?.Invoke(true, updateFailFiles);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<UpdateFailFile>());
                }
            };
            if(async)
                CallP4("update", callAction_, dir);
            else
            {
                SyncCallP4("update", callAction_, dir);
            }
        }
        
        public static void CheckoutOrAdd(string filePath, Action<bool, string> callback)
        {
            CallP4("checkout_or_add", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, filePath: filePath);
        }
        
        public static void MarkForDelete(string filePath, Action<bool, string> callback)
        {
            CallP4("mark_for_delete", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, filePath: filePath);
        }

        public static void SyncForce(string filePath, Action<bool, string> callback)
        {
            CallP4("update_f", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, filePath: filePath);
        }

        public static void SyncForceUpdate(string dir, Action<bool, List<UpdateFailFile>> callback, int timeOut = -1)
        {
            SyncCallP4("updateF", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var updateFailFiles = new List<UpdateFailFile>();
                    try
                    {
                        var strs = result.Split('|');
                        foreach (var s in strs)
                        {
                            if (string.IsNullOrEmpty(s) || s.Contains("up-to-date") || s.Contains("no such file"))
                                continue;
                            var info = s.TrimStart().TrimEnd();
                            if (string.IsNullOrEmpty(info) || !info.Contains(" - ")) continue;
                            var infos = info.Split(" - ")[1];
                            var reason = infos.Split(" file ")[0];
                            var file = infos.Split(" file ")[1];
                            updateFailFiles.Add(new UpdateFailFile() { reason = reason, file = file });
                        }
                    }
                    catch (Exception e)
                    {
                        UnityEngine.Debug.LogException(e);
                    }
                    callback?.Invoke(true, updateFailFiles);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<UpdateFailFile>());
                }
            }, dir, timeOut: timeOut);
        }
        
        public static void SyncUpdate(string dir, Action<bool, List<UpdateFailFile>> callback)
        {
            SyncCallP4("update", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var updateFailFiles = new List<UpdateFailFile>();
                    var strs = result.Split('|');
                    foreach (var s in strs)
                    {
                        if (string.IsNullOrEmpty(s) || s.Contains("up-to-date") || s.Contains("no such file")) continue;
                        var info = s.TrimStart().TrimEnd();
                        if (string.IsNullOrEmpty(info) || !info.Contains(" - ")) continue;
                        var infos = info.Split(" - ")[1];
                        var reason = infos.Split(" file ")[0];
                        var file = infos.Split(" file ")[1];
                        updateFailFiles.Add(new UpdateFailFile() { reason = reason, file = file });
                    }
                    callback?.Invoke(true, updateFailFiles);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<UpdateFailFile>());
                }
            }, dir);
        }
        
        public static void SyncUpdate(List<string> fileList, Action<bool, List<UpdateFailFile>> callback)
        {
            SyncCallP4("updateFiles", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var updateFailFiles = new List<UpdateFailFile>();
                    var strs = result.Split('|');
                    foreach (var s in strs)
                    {
                        if (string.IsNullOrEmpty(s) || s.Contains("up-to-date") || s.Contains("no such file")) continue;
                        var info = s.TrimStart().TrimEnd();
                        if (string.IsNullOrEmpty(info) || !info.Contains(" - ")) continue;
                        var infos = info.Split(" - ")[1];
                        var fileInfoList = infos.Split(" file ");
                        var reason = fileInfoList[0];
                        if(fileInfoList.Length < 2)
                            continue;
                        var file = fileInfoList[1];
                        updateFailFiles.Add(new UpdateFailFile() { reason = reason, file = file });
                    }
                    callback?.Invoke(true, updateFailFiles);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<UpdateFailFile>());
                }
            }, "",SaveFileList(fileList,"updateFiles"));
        }
        
        public static void SyncGetFilesResolveInfo(List<string> fileList, Action<bool, List<string>> callback)
        {
            SyncCallP4("get_resolvefiles_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    List<string> valList = new List<string>();
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            if (obj.Keys.Contains("clientFile"))
                            {
                                if (obj["clientFile"] != null && !string.IsNullOrEmpty(obj["clientFile"].ToString()))
                                {
                                    valList.Add( obj["clientFile"].ToString().Replace("\\","/"));
                                }
                            }
                        }
                    }
                    callback?.Invoke(true,valList);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<string>());
                }
            }, "",SaveFileList(fileList,"get_resolvefiles_info"));
        }

        public static void SyncLockFiles(List<string> fileList, Action<bool> callback, int timeOut = -1)
        {
            List<FstatFileInfo> HasLockedList = new List<FstatFileInfo>();
            bool canLock = false;
            SyncCallP4("fstatFiles", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var changeFile = new FstatFileInfo
                            {
                                clientFile = obj["clientFile"].ToString().Replace("\\","/"),
                            };
                            if (obj.Keys.Contains("otherLock"))
                            {
                                changeFile.lockType = LockType.LockByOther;
                                if (obj["otherLock"] != null && !string.IsNullOrEmpty(obj["otherLock"].ToString()))
                                {
                                    foreach (var locker in obj["otherLock"])
                                    {
                                        if (locker != null && !string.IsNullOrEmpty(locker.ToString()))
                                        {
                                            changeFile.lockerName = locker.ToString();
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                else
                {
                    ShowError(result);
                    canLock = false;
                }
            }, "", SaveFileList(fileList, "fstatFiles"), timeOut: timeOut);

            SyncCallP4("lockFiles", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "", SaveFileList(fileList, "lockFiles"), timeOut: timeOut);
        }
        public static void SyncRevert_K_Files(List<string> fileList, Action<bool> callback)
        {
            SyncCallP4("revert_K_Files", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    
                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "",SaveFileList(fileList,"revert_K_Files"));
        }
        
        public static void SyncRevertFiles(List<string> fileList, Action<bool> callback)
        {
            SyncCallP4("revertFiles", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    
                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "",SaveFileList(fileList,"revertFiles"));
        }
        //file_reversion
        public static void UndoReversionFile(List<string> fileList, Action<bool> callback)
        {
            bool isvalid = !fileList.IsNullOrEmpty() && fileList.All(t => !string.IsNullOrEmpty(t));
            if (!isvalid)
            {
                ShowError("文件路径列表错误");
                callback?.Invoke(false);
                return;
            }
            P4Utils.CallP4("undo_reversion", result =>
            {
                if (!result.Contains("Error"))
                {

                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "", P4Utils.SaveFileList(fileList, "undo_reversion"));
        }

        public static void RevertAndGetLastversion(List<string> fileList, Action<bool> callback)
        {
            bool isvalid = !fileList.IsNullOrEmpty() && fileList.All(t => !string.IsNullOrEmpty(t));
            if (!isvalid)
            {
                ShowError("文件路径列表错误");
                callback?.Invoke(false);
                return;
            }

            CallP4("revert_getlastversion", result =>
            {
                if (!result.Contains("Error"))
                {

                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "", P4Utils.SaveFileList(fileList, "revert_getlastversion"));
        }

        public static void SyncUnLockFiles(List<string> fileList, Action<bool> callback, int timeOut = -1)
        {
            SyncCallP4("unLockFiles", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    List<string> valList = new List<string>();
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            
                        }
                    }
                    callback?.Invoke(true);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false);
                }
            }, "",SaveFileList(fileList,"unLockFiles"), timeOut: timeOut);
        }
        
        public static void CommitFiles(List<string> files, string msg, Action<bool, string> callback)
        {
            CallP4("commitFiles", (result) =>
            {
                EditorCommonLogger.LogInfo("CommitFiles result:" + result);
                //提交失败的时候  有可能会返回空串
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, "", SaveFileList(files, "CommitFiles"), msg);
        }

        /// <summary>
        /// 拉起多分支提交界面，提交文件到指定分支。注意这里的分支是p4的分支概念，不是git的分支概念。
        /// </summary>
        /// <param name="branchName"></param>
        /// <param name="files"></param>
        /// <param name="msg"></param>
        /// <param name="callback"></param>
        public static void CallBranchCommitFiles(List<string> files, string msg,
            Action<bool, string> callback)
        {
            CallP4("branchCommitFiles", (result) =>
                {
                    EditorCommonLogger.LogInfo("BranchCommitFiles result:" + result);
                    //提交失败的时候  有可能会返回空串
                    if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                        callback?.Invoke(true, result);
                    else
                    {
                        ShowError(result);
                        callback?.Invoke(false, result);
                    }
                }, "", SaveFileList(files, "BranchCommitFiles"), msg, revertFileMetaBeforeSubmit: true,
                revertFilesBeforeSubmit: false);
        }
        
        public static void SyncCommitFiles(List<string> files, string msg, Action<bool, string> callback)
        {
            SyncCallP4("commitFiles", (result) =>
            {
                EditorCommonLogger.LogInfo("CommitFiles result:" + result);
                //提交失败的时候  有可能会返回空串
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, "", SaveFileList(files, "CommitFiles"), msg);
        }

        // [MenuItem("Test/CheckMetaFilesGUIDModified")]
        // public static void Test()
        // {
        //     CheckMetaFilesGUIDModified(new List<string>()
        //     {
        //         "c:\\FunplusWorldX\\3Day\\P4\\unity_project\\Assets\\AddressableAssetsData\\AddressDir.asset.meta",
        //         "c:\\FunplusWorldX\\3Day\\P4\\unity_project\\Assets\\AddressableAssetsData\\AddressDir.asset.meta",
        //         "c:\\FunplusWorldX\\3Day\\P4\\unity_project\\Assets\\AddressableAssetsData\\AddressDir.asset.meta",
        //     }, (bOk, ret) =>
        //     {
        //         if (bOk)
        //             UnityEngine.Debug.Log("CheckMetaFilesGUIDModified Success");
        //         else
        //             UnityEngine.Debug.Log($"CheckMetaFilesGUIDModified Fail: {ret}");
        //     });
        // }
        
        public static void CheckMetaFilesGUIDModified(List<string> files, Action<bool, string> callback)
        {
            SyncCallP4("checkMetasGuidModified", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    callback?.Invoke(true, "");
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, filePath: SaveFileList(files, "CheckMetaFiles"));
        }

        public static void FilesAddToPendingList(List<string> files, string changeId, string msg,
            Action<bool, string> callback)
        {
            // Reconcile模式：只会把检测到有变更的文件加入目标changelist。
            CallP4("p4_add_to_changelist", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, "", SaveFileList(files, "PendingList"), msg, changeId);
        }

        public static void FilesCheckoutOrAddToPendingList(List<string> files, string changeId, string msg,
            Action<bool, string> callback)
        {
            // Checkout/Add模式：即使文件内容无diff，也可以放入目标changelist。
            CallP4("checkout_or_add_to_changelist", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, "", SaveFileList(files, "PendingListCheckoutOrAdd"), msg, changeId);
        }
        
        public static void CommitDir(string dir, string msg, Action<bool, string> callback)
        {
            CallP4("commitDir", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, dir, "", msg);
        }
        
        public static void SyncCommitDir(string dir, string msg, Action<bool, string> callback)
        {
            SyncCallP4("commitDir", (result) =>
            {
                if (!result.Contains("Error"))
                    callback?.Invoke(true, result);
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, result);
                }
            }, dir, "", msg);
        }
        
        public static void GetDirChangeFiles(string dir, Action<bool, List<ChangeFileInfo>> callback,bool _async = true)
        {
            Action<string> callAction_ = (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var list = new List<ChangeFileInfo>();
                    if (string.IsNullOrEmpty(result))
                    {
                        ShowError($"Error 调用P4 Reconcile结果为空！");
                        callback?.Invoke(false, list);
                    }
                    else
                    {
                        JsonData jsonObject = JsonMapper.ToObject(result);
                        for (int i = 0; i < jsonObject.Count; ++i)
                        {
                            var obj = jsonObject[i];
                            if (!obj.IsString)
                            {
                                var changeFile = new ChangeFileInfo
                                {
                                    clientFile = obj["clientFile"].ToString().Replace("\\", "/"),
                                    depotFile = obj["depotFile"].ToString(),
                                    workRev = obj["workRev"].ToString(),
                                    action = obj["action"].ToString(),
                                    type = obj["type"].ToString(),
                                    select = true
                                };
                                list.Add(changeFile);
                            }
                        }
                        callback?.Invoke(true, list);
                    }
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<ChangeFileInfo>());
                }
            };
            if (_async)
                CallP4("get_all_change_file", callAction_, dir);
            else
                SyncCallP4("get_all_change_file", callAction_, dir);
        }
        public static void GetDirLatestInfo(string dir, Action<bool, LatestInfo> callback)
        {
            CallP4("get_latest_all_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    var LatestInfo = new LatestInfo()
                    {
                        change = jsonObject["change"].ToString(),
                        client = jsonObject["client"].ToString(),
                        desc = jsonObject["desc"].ToString(),
                        time = jsonObject["time"].ToString(),
                        user = jsonObject["user"].ToString(),
                    };
                    callback?.Invoke(true, LatestInfo);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new LatestInfo());
                }
            }, dir);
        }

        public static void SyncGetDirLatestInfo(string dir, Action<bool, LatestInfo> callback)
        {
            SyncCallP4("get_latest_all_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    var LatestInfo = new LatestInfo()
                    {
                        change = jsonObject["change"].ToString(),
                        client = jsonObject["client"].ToString(),
                        desc = jsonObject["desc"].ToString(),
                        time = jsonObject["time"].ToString(),
                        user = jsonObject["user"].ToString(),
                    };
                    callback?.Invoke(true, LatestInfo);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new LatestInfo());
                }
            }, dir);
        }
        
        

        public static void SyncGetDirLatestCommiterInfo(string dir, Action<bool, string> callback)
        {
            SyncCallP4("get_latest_all_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    var desc = jsonObject["desc"].ToString();
                    Regex regex = new Regex(@"--user=(.*?)\s+");
                    Match match = regex.Match(desc);
                    var tapdUser = "";
                    if (match.Success)
                    {
                        tapdUser = match.Groups[1].Value;
                    }
                    else
                    {
                        var user = jsonObject["user"].ToString();
                        var client = jsonObject["client"].ToString();
                        tapdUser = $"{user}@{client}";
                    }

                    callback?.Invoke(true, tapdUser);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, "NotFound Author");
                }
            }, dir);
        }

        public static void SyncGetDirLatestUserEmailInfo(string dir, Action<bool, string> callback, int depth = 1)
        {
            SyncCallP4("get_changes_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var desc = obj["desc"].ToString();
                            Regex regex = new Regex(@"--user=(.*?)\s+");
                            Match match = regex.Match(desc);
                            var tapdUser = "";
                            if (match.Success)
                            {
                                tapdUser = GetLarkUserEmailByTapdUser(match.Groups[1].Value);
                                callback?.Invoke(true,
                                    string.IsNullOrEmpty(tapdUser) ? match.Groups[1].Value : tapdUser);
                                break;
                            }
                        }
                    }
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, "NotFound tapdUser");
                }
            }, dir, max: depth);
        }

        public static void SyncGetDirLatestUserNameInfos(string dir, Action<bool, List<string>> callback,
            int depth = 10)
        {
            SyncCallP4("get_changes_info", (result) =>
            {
                if (!result.Contains("Error"))
                {
                    var users = new List<string>();
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var desc = obj["desc"].ToString();
                            Regex regex = new Regex(@"--user=(.*?)\s+");
                            Match match = regex.Match(desc);
                            var tapdUser = "";
                            if (match.Success)
                            {
                                users.Add(GetLarkUserNameByTapdUser(match.Groups[1].Value));
                            }
                        }
                    }

                    callback?.Invoke(true, users.Distinct().ToList());
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<string>() { "Not Found User" });
                }
            }, dir, max: depth);
        }
        
        public static string GetLarkUserEmailByTapdUser(string tapdUser)
        {
            try
            {
                string url = "http://10.8.45.67:8080/api/basic/user/tapd";
                using (var client = new HttpClient())
                {
                    var response = client.GetAsync($"{url}?tapd_name={tapdUser}").Result;
                    if (response.IsSuccessStatusCode)
                    {
                        string content = response.Content.ReadAsStringAsync().Result;
                        JObject data = JObject.Parse(content);
                        return data["data"]?["user_email"]?.ToString();
                    }
                    else
                    {
                        return null;
                    }
                }
            }
            catch (Exception e)
            {
                // Optionally, log the exception e
                return null;
            }
        }

        public static string GetLarkUserNameByTapdUser(string tapdUser)
        {
            try
            {
                string url = "http://10.8.45.67:8080/api/basic/user/tapd";
                using (var client = new HttpClient())
                {
                    var response = client.GetAsync($"{url}?tapd_name={tapdUser}").Result;
                    if (response.IsSuccessStatusCode)
                    {
                        string content = response.Content.ReadAsStringAsync().Result;
                        JObject data = JObject.Parse(content);
                        return data["data"]?["user_name"]?.ToString();
                    }
                    else
                    {
                        return null;
                    }
                }
            }
            catch (Exception e)
            {
                // Optionally, log the exception e
                return null;
            }
        }
        
        public static void CheckFileExistsOnServer(string filePath, Action<bool, List<UpdateFailFile>> callback)
        {
            List<string> fileList = new List<string> { filePath };

            SyncCallP4("fstatFiles", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    var updateFailFiles = new List<UpdateFailFile>();
                    JsonData jsonObject = JsonMapper.ToObject(result);

                    bool fileExists = false;

                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString && obj.Keys.Contains("depotFile"))
                        {
                            fileExists = true;
                            break;
                        }
                    }

                    if (fileExists)
                    {
                        callback?.Invoke(true, updateFailFiles);
                    }
                    else
                    {
                        updateFailFiles.Add(new UpdateFailFile() { reason = "File not found on server", file = filePath });
                        callback?.Invoke(false, updateFailFiles);
                    }
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<UpdateFailFile>());
                }
            }, "", SaveFileList(fileList, "fstatFiles"));
        }


        // [MenuItem("Test/SyncGetDirCommiterInfo")]
        // private static void Test()
        // {
        //     SendDDMsgUserEmail("zhengmeng.pei@funplus.com", "Unity C# 飞书通知测试！");
        //     SendDDMsg("oc_cc97fabb070cda26821e888370f4caa5","Unity C# 飞书群通知测试！");
        // }
        
         public static void SyncGetFilesInfoByDir(string dirPath, Action<bool, List<FstatFileInfo>> callback)
        {
            List<FstatFileInfo> newList = new List<FstatFileInfo>();
            SyncCallP4("fstatDir", (result) =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var changeFile = new FstatFileInfo
                            {
                                clientFile = obj["clientFile"].ToString().Replace("\\","/"),
                            };
                            if (obj.Keys.Contains("otherLock"))
                            {
                                changeFile.lockType = LockType.LockByOther;
                                if (obj["otherLock"] != null && !string.IsNullOrEmpty(obj["otherLock"].ToString()))
                                {
                                    foreach (var locker in obj["otherLock"])
                                    {
                                        if (locker != null && !string.IsNullOrEmpty(locker.ToString()))
                                        {
                                            changeFile.lockerName = locker.ToString();
                                        }
                                    }
                                }
                            }
                            else if (obj.Keys.Contains("ourLock"))
                            {
                                changeFile.lockType = LockType.LockBySelf;
                            }
                            else
                            {
                                changeFile.lockType = LockType.NoLock;
                            }
                           
                            newList.Add(changeFile);
                        }
                    }

                    callback?.Invoke(true, newList);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, new List<FstatFileInfo>());
                }
            }, dirPath);
        }

         public static void SyncGetFilesInfo(List<string> fileList, Action<bool, List<FstatFileInfo>> callback,
             int timeOut = -1)
         {
             List<FstatFileInfo> newList = new List<FstatFileInfo>();
             if (fileList.Count == 0)
             {
                 callback?.Invoke(true, newList);
                 return;
             }

             SyncCallP4("fstatFiles", (result) =>
             {
                 if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                 {
                     JsonData jsonObject = JsonMapper.ToObject(result);
                     for (int i = 0; i < jsonObject.Count; ++i)
                     {
                         var obj = jsonObject[i];
                         if (!obj.IsString)
                         {
                             var changeFile = new FstatFileInfo
                             {
                                 clientFile = obj["clientFile"].ToString().Replace("\\", "/"),
                             };
                             if (obj.Keys.Contains("otherLock"))
                             {
                                 changeFile.lockType = LockType.LockByOther;
                                 if (obj["otherLock"] != null && !string.IsNullOrEmpty(obj["otherLock"].ToString()))
                                 {
                                     foreach (var locker in obj["otherLock"])
                                     {
                                         if (locker != null && !string.IsNullOrEmpty(locker.ToString()))
                                         {
                                             changeFile.lockerName = locker.ToString();
                                         }
                                     }
                                 }
                             }
                             else if (obj.Keys.Contains("ourLock"))
                             {
                                 changeFile.lockType = LockType.LockBySelf;
                             }
                             else
                             {
                                 changeFile.lockType = LockType.NoLock;
                             }

                             if (obj.Keys.Contains("headAction"))
                             {
                                 changeFile.headAction = obj["headAction"].ToString();
                             }

                             newList.Add(changeFile);
                         }
                     }

                     callback?.Invoke(true, newList);
                 }
                 else
                 {
                     ShowError(result);
                     callback?.Invoke(false, new List<FstatFileInfo>());
                 }
             }, "", SaveFileList(fileList, "fstatFiles"), timeOut: timeOut);
         }

        public static void PrintFile(ChangeFileInfo changeFileInfo, Action<bool, string> callback)
        {
            SyncCallP4("p4_print_file", (result) =>
                {
                    if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                    {
                        callback?.Invoke(true, result);
                    }
                    else
                    {
                        ShowError(result);
                        callback?.Invoke(false, "");
                    }
                }, "", $"{changeFileInfo.depotFile}#{changeFileInfo.workRev}",
                "");
        }

        [DllImport("kernel32.dll")]
        private static extern int GetACP();

        public static Encoding GetCurEncoding()
        {
            if (Environment.OSVersion.Platform == PlatformID.MacOSX || 
                Environment.OSVersion.Platform == PlatformID.Unix)
            {
                return Encoding.UTF8;
            }

            int ansiCodePage = GetACP();
            Encoding ansiEncoding = Encoding.GetEncoding(ansiCodePage);
            //UnityEngine.Debug.Log($"当前系统编码：{ansiEncoding.WebName}");
            return ansiEncoding;
        }

        public static void SyncGetLocalChangelist(Action<bool, List<ChangeListInfo>> callback)
        {
            SyncCallP4("p4_get_local_changelist", (result) =>
            {
                var list = new List<ChangeListInfo>();
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        var changeInfo = new ChangeListInfo()
                        {
                            changeId = obj["change"].ToString(),
                            desc = obj["desc"].ToString(),
                        };
                        list.Add(changeInfo);
                    }

                    callback?.Invoke(true, list);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, list);
                }
            });
        }

        private static HttpClient httpClient = new();

        private static async void PostSendMsg(string type, string target, string msg)
        {
            try
            {
                var jsonObj = new JsonData();
                jsonObj["type"] = type;
                jsonObj["target"] = target;
                jsonObj["msg"] = msg;
                var content = new StringContent(JsonMapper.ToJson(jsonObj), Encoding.UTF8, "application/json");
                var response = await httpClient.PostAsync("http://10.8.45.67:3106/lark_tools_send_msg", content);
                response.EnsureSuccessStatusCode();
                var ret = await response.Content.ReadAsStringAsync();
                UnityEngine.Debug.Log($"[SendDDMsg] 发送成功: {ret}");
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogError($"[SendDDMsg] 发送失败 (type={type}, target={target}): {e.Message}");
            }
        }
        
        public static string GetLarkUserOpendIdByUserName(string userName)
        {
            try
            {
                string url = "http://10.8.45.67:8080/api/auth/users";
                using (var client = new HttpClient())
                {
                    var response = client.GetAsync($"{url}?searchKey={userName}&departmentId=0&pageNum=1&pageSize=-1").Result;
                    if (response.IsSuccessStatusCode)
                    {
                        string content = response.Content.ReadAsStringAsync().Result;
                        JObject data = JObject.Parse(content);
                        return data["data"]?["list"][0]?["user_lark_open_id"].ToString();
                    }
                    else
                    {
                        return null;
                    }
                }
            }
            catch (Exception e)
            {
                // Optionally, log the exception e
                return null;
            }
        }

        /// <summary>
        /// 通过用户名一次请求同时获取飞书 openId 和邮箱，避免重复调用接口。
        /// </summary>
        public static (string openId, string email) GetLarkUserInfoByUserName(string userName)
        {
            try
            {
                string url = "http://10.8.45.67:8080/api/auth/users";
                using (var client = new HttpClient())
                {
                    var response = client.GetAsync($"{url}?searchKey={userName}&departmentId=0&pageNum=1&pageSize=-1").Result;
                    if (response.IsSuccessStatusCode)
                    {
                        string content = response.Content.ReadAsStringAsync().Result;
                        JObject data = JObject.Parse(content);
                        var user = data["data"]?["list"]?[0];
                        string openId = user?["user_lark_open_id"]?.ToString();
                        string email = user?["user_email"]?.ToString();
                        return (openId, email);
                    }
                }
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogWarning($"[P4Utils] GetLarkUserInfoByUserName failed: {e.Message}");
            }

            return (null, null);
        }

        private static void SyncPostSendMsg(string type, string target, string msg)
        {
            var jsonObj = new JsonData();
            jsonObj["type"] = type;
            jsonObj["target"] = target;
            jsonObj["msg"] = msg;
            var content = new StringContent(JsonMapper.ToJson(jsonObj), Encoding.UTF8, "application/json");
            var response = httpClient.PostAsync("http://10.8.45.67:3106/lark_tools_send_msg", content);
            response.Wait();
            UnityEngine.Debug.Log(response.Result.StatusCode);
        }

        public static void SyncSendDDMsgUserEmail(string email, string msg)
        {
            SyncPostSendMsg("user", email, msg);
        }

        public static void SyncSendDDMsg(string larkChatId, string msg)
        {
            SyncPostSendMsg("group", larkChatId, msg);
        }
        
        public static void SendDDMsgUserEmail(string email, string msg)
        {
            PostSendMsg("user", email, msg);
        }

        public static void SendDDMsg(string larkChatId, string msg)
        {
            PostSendMsg("group", larkChatId, msg);
        }
        
        public static string GetProjectPath()
        {
            return Application.dataPath.Replace("Assets", "");
        }

        public static async void CallP4(string cmd, Action<string> callback, string dir = "", string filePath = "",
            string msg = "", string changeId = "", int max = 5, string email = "", string larkChatId = "",
            bool revertFilesBeforeSubmit = false, bool revertFileMetaBeforeSubmit = false)
        {
            try
            {
                var errorInfo = "";
                if (string.IsNullOrEmpty(UserName) || string.IsNullOrEmpty(WorkSpace))
                    errorInfo = "Error 获取P4信息失败，未能执行P4操作，请确认Unity - Window - P4 中已经正确配置P4信息";
                if (string.IsNullOrEmpty(cmd)) errorInfo = "Error 不能执行命令空！";
                if (cmd != "p4_get_local_changelist" && cmd != "check_client_into" && cmd != "send_ddMsg_user" &&
                    cmd != "send_ddMsg")
                {
                    if (string.IsNullOrEmpty(dir) && string.IsNullOrEmpty(filePath)) errorInfo = "Error 没有指定目标目录或者文件！";
                }
                if (string.IsNullOrEmpty(errorInfo))
                {
                    var retLogFile = GetRetLogFilePath();
                    if (File.Exists(retLogFile))
                    {
                        File.Delete(retLogFile);
                    }
                    var cmdLine = GetCmdLine(cmd, retLogFile, dir, filePath, msg, changeId, max, email, larkChatId, revertFilesBeforeSubmit, revertFileMetaBeforeSubmit);
                    var process = StartPythonProcess(cmdLine);
                    Task processTask = Task.Run(() =>
                    {
                        process.WaitForExit();
                    });
                    await Task.WhenAll(processTask);
                    var ret = "";
                    if (File.Exists(retLogFile))
                    {
                        ret = File.ReadAllText(retLogFile, Encoding.UTF8);
                        File.Delete(retLogFile);
                    }
                    // UnityEngine.Debug.Log(ret);
                    callback?.Invoke(GetRetrunStr(ret));
                }
                else
                {
                    callback?.Invoke(errorInfo);
                }
            }
            catch (System.Exception e)
            {
                UnityEngine.Debug.LogException(e);
                callback?.Invoke($"Error 调用P4Tool.py出现意外\n{e.Message}\n{e.StackTrace}");
            }
        }

        private static int retLogIndex = 0;

        private static string GetRetLogFilePath()
        {
            return $"{GetProjectPath()}p4_tool_ret_{retLogIndex++}.txt";
        }
        
        // 现在Mac 几台测试机都是外挂硬盘，P4路径和真实路径不一致 这里特殊处理一下吧
        // todo 如果后续有大量Mac测试机考虑部署环境的时候按照一套统一规则来
        private static Dictionary<string,string> MacPathReplaceDict = new Dictionary<string, string>()
        {
            {"/Volumes/ShowyMacExt/dev/p4dir/v001", "/Users/showy/data/dev/p4dir/v001"}
        };

        private static string GetCmdLine(string cmd, string retLogFile, string dir = "", string filePath = "",
            string msg = "", string changeId = "", int max = 5, string email = "", string larkChatId = "",
            bool revertFilesBeforeSubmit = false, bool revertFileMetaBeforeSubmit = false)
        {
            var line = ($"{GetP4ToolDirPath()}/P4Tool.py --p4user {UserName} --p4workspace {WorkSpace} --cmd {cmd} " +
                        $"{(string.IsNullOrEmpty(dir) ? "" : $"--dir {dir}")} " +
                        $"{(string.IsNullOrEmpty(filePath) ? "" : $"--filePath \"{filePath}\"")} " +
                        $"{(string.IsNullOrEmpty(msg) ? "" : $"--msg \"{msg}\"")} " +
                        $"{(string.IsNullOrEmpty(changeId) ? "" : $"--changeId \"{changeId}\"")} " +
                        $"{(string.IsNullOrEmpty(email) ? "" : $"--email \"{email}\"")} " +
                        $"{(string.IsNullOrEmpty(larkChatId) ? "" : $"--larkChatId \"{larkChatId}\"")} " +
                        $"--logFile {GetProjectPath()}p4tool.log " +
                        $"--retLogFile {retLogFile} " +
                        $"--p4Root {GetCurrP4Root()} " +
                        $"--revertFilesBeforeSubmit {(revertFilesBeforeSubmit ? 1 : 0)} " +
                        $"--revertFileMetaBeforeSubmit {(revertFileMetaBeforeSubmit ? 1 : 0)} " +
                        $"--max \"{max}\"");
            if (Environment.OSVersion.Platform == PlatformID.MacOSX ||
                Environment.OSVersion.Platform == PlatformID.Unix)
            {
                foreach (var item in MacPathReplaceDict)
                {
                    line = line.Replace(item.Key, item.Value);
                }
                return $"python3 {line}";
            }

            return line;
        }

        public static string GetCurrP4Root()
        {
            return Directory.GetParent(Application.dataPath.Replace("/Assets", "")).FullName.Replace("//", "/")
                .Replace("\\", "/");
        }

        public static void CheckP4Root(Action<string> callback)
        {
            SyncCallP4("check_client_into", callback);
        }

        public static void SyncCallP4(string cmd, Action<string> callback, string dir = "", string filePath = "",
            string msg = "", string changeId = "", int max = 5, string email = "", string larkChatId = "",
            int timeOut = -1, bool revertFilesBeforeSubmit = false, bool revertFileMetaBeforeSubmit = false)
        {
            try
            {
                var errorInfo = "";
                if (string.IsNullOrEmpty(UserName) || string.IsNullOrEmpty(WorkSpace))
                    errorInfo = "Error 获取账号和工作区信息失败，未能执行P4操作，请到Unity中Window/P4/设置P4信息的页面确认已经正确配置";
                if (string.IsNullOrEmpty(cmd)) errorInfo = "Error 不能执行命令空！";
                if (cmd != "p4_get_local_changelist" && cmd != "check_client_into" && cmd != "send_ddMsg_user" &&
                    cmd != "send_ddMsg")
                {
                    if (string.IsNullOrEmpty(dir) && string.IsNullOrEmpty(filePath)) errorInfo = "Error 没有指定目标目录或者文件！";
                }
                if (string.IsNullOrEmpty(errorInfo))
                {
                    var retLogFile = GetRetLogFilePath();
                    if (File.Exists(retLogFile))
                    {
                        File.Delete(retLogFile);
                    }
                    var cmdLine = GetCmdLine(cmd, retLogFile, dir, filePath, msg, changeId, max, email, larkChatId, revertFilesBeforeSubmit, revertFileMetaBeforeSubmit);
                    var process = StartPythonProcess(cmdLine);
                    process.WaitForExit(timeOut);
                    var ret = "";
                    if (File.Exists(retLogFile))
                    {
                        ret = File.ReadAllText(retLogFile, Encoding.UTF8);
                        File.Delete(retLogFile);
                    }
                    // UnityEngine.Debug.Log(ret);
                    callback?.Invoke(GetRetrunStr(ret));
                }
                else
                {
                    callback?.Invoke(errorInfo);
                }
            }
            catch (System.Exception e)
            {
                UnityEngine.Debug.LogException(e);
                callback?.Invoke($"Error 调用P4Tool.py出现意外\n{e.Message}\n{e.StackTrace}");
            }
        }

        private static Process StartPythonProcess(string cmd)
        {
            if (Environment.OSVersion.Platform == PlatformID.MacOSX ||
                Environment.OSVersion.Platform == PlatformID.Unix)
            {
                return Process.Start("/bin/bash", $"-cl '{cmd}'");
            }
            else
            {
                var startInfo = new ProcessStartInfo();
                startInfo.FileName = GetPythonExePath();
                startInfo.Arguments = cmd;
                startInfo.UseShellExecute = false;
                startInfo.CreateNoWindow = true;
                startInfo.WindowStyle = ProcessWindowStyle.Hidden;
                return Process.Start(startInfo);
            }
        }
            

        public static void ShowDiff(ChangeFileInfo fileInfo)
        {
            var fileName = Path.GetFileName(fileInfo.clientFile);
            var tempPath = Path.Combine(Application.dataPath.Replace("Assets", "Temp"), fileName);
            var deportPath = fileInfo.depotFile;
            var bat = Path.Combine(GetP4ToolDirPath(), "ShowDiff.bat");
            ProcessStartInfo start = new()
            {
                FileName = bat,
                Arguments = $"\"{tempPath}\" \"{deportPath}\"  \"{fileInfo.clientFile}\"",
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };
            UnityEngine.Debug.Log(start.Arguments);
            Process process = Process.Start(start);
        }
        
        public static string GetPythonExePath(string exeName = "python.exe")
        {
            var ProjectPath = Directory.GetParent(Application.dataPath);
            var path = Path.Combine(ProjectPath.FullName.Replace("unity_project", "tools"), "Python37/python.exe");
            if (File.Exists(path))
            {
                return path;
            }
            throw new Exception($"获取{exeName}的路径失败！请及时更新P4仓库，请更新tools目录");
        }

        public static string GetPythonExePath(EnvironmentVariableTarget target, string exeName)
        {
            string pathStr = Environment.GetEnvironmentVariable("Path", target);
            string[] paths = pathStr.Split(';');
            string path = "";
            for (int i = 0; i < paths.Length; i++)
            {
                //这个目录下可能会拿到错误的exe
                if (paths[i].Contains("WindowsApps"))
                {
                    continue;
                }
                UnityEngine.Debug.Log(paths[i]);
                string t = "";
                if (paths[i].EndsWith("\\"))
                {
                    t = paths[i] + exeName;
                }
                else
                {
                    t = paths[i] + "\\" + exeName;
                }
                if (System.IO.File.Exists(t))
                {
                    path = t;
                    break;
                }
            }
            UnityEngine.Debug.Log(path);
            return path;
        }

        private static string GetP4ToolDirPath()
        {
            return Application.dataPath.Replace("Assets", "Packages/com.funplus.worldx.editor-common/Editor/Python");
        }

        private static void ShowError(string errorInfo)
        {
            // if (errorInfo.Contains("不是同一个！"))
            // {
            //     
            // }
            UnityEngine.Debug.LogError("P4:" + errorInfo);
        }

        private static string GetRetrunStr(string input)
        {
            if (Environment.OSVersion.Platform == PlatformID.MacOSX ||
                Environment.OSVersion.Platform == PlatformID.Unix)
            {
                foreach (var item in MacPathReplaceDict)
                {
                    input = input.Replace(item.Value, item.Key);
                }
            }

            if (input.Contains("returnStrStart") && input.Contains("returnStrEnd"))
            {
                string start = "returnStrStart";
                string end = "returnStrEnd";

                int startIndex = input.IndexOf(start) + start.Length;
                int endIndex = input.IndexOf(end, startIndex);

                if (startIndex >= 0 && endIndex >= 0)
                {
                    string result = input[startIndex..endIndex];
                    return result;
                }
                else
                {
                    return input;
                }
            }
            else
            {
                return input;
            }
        }

        public static void CheckFileListEditState(List<ChangeFileInfo> list, Action<bool, List<ChangeFileInfo>> callback)
        {
            List<ChangeFileInfo> newList = new List<ChangeFileInfo>();
           

            CallP4("get_all_change_file_by_pathList", (result) =>
            {
                //提交失败的时候有可能会返回空串
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var changeFile = new ChangeFileInfo
                            {
                                clientFile = obj["clientFile"].ToString().Replace("\\","/"),
                                depotFile = obj["depotFile"].ToString(),
                                workRev = obj["workRev"].ToString(),
                                action = obj["action"].ToString(),
                                type = obj["type"].ToString(),
                                select = true
                            };
                            newList.Add(changeFile);
                        }
                    }
                    callback?.Invoke(true, newList);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, newList);
                }
            }, "", SaveFileList(list.Select((info => info.clientFile)).ToList(), "Reconcile"),"");
        }

        public static void SyncCheckFileListEditState(List<string> list, Action<bool, List<ChangeFileInfo>> callback, int timeOut = -1)
        {
            List<ChangeFileInfo> newList = new List<ChangeFileInfo>();

            SyncCallP4("get_all_change_file_by_pathList", (result) =>
            {
                //提交失败的时候有可能会返回空串
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    JsonData jsonObject = JsonMapper.ToObject(result);
                    for (int i = 0; i < jsonObject.Count; ++i)
                    {
                        var obj = jsonObject[i];
                        if (!obj.IsString)
                        {
                            var changeFile = new ChangeFileInfo
                            {
                                clientFile = obj["clientFile"].ToString().Replace("\\", "/"),
                                depotFile = obj["depotFile"].ToString(),
                                workRev = obj["workRev"].ToString(),
                                action = obj["action"].ToString(),
                                type = obj["type"].ToString(),
                                select = true
                            };
                            newList.Add(changeFile);
                        }
                    }

                    callback?.Invoke(true, newList);
                }
                else
                {
                    ShowError(result);
                    callback?.Invoke(false, newList);
                }
            }, "", SaveFileList(list, "Reconcile"), "",timeOut:timeOut);
        }

        public static string execCMD(string command)
        {
            System.Diagnostics.Process pro = new System.Diagnostics.Process();
            pro.StartInfo.FileName = "cmd.exe";
            pro.StartInfo.UseShellExecute = false;
            pro.StartInfo.RedirectStandardError = true;
            pro.StartInfo.RedirectStandardInput = true;
            pro.StartInfo.RedirectStandardOutput = true;
            pro.StartInfo.CreateNoWindow = true;
            pro.Start();
            pro.StandardInput.WriteLine(command);
            pro.StandardInput.WriteLine("exit");
            pro.StandardInput.AutoFlush = true;
            //获取cmd窗口的输出信息
            string output = pro.StandardOutput.ReadToEnd();
            pro.WaitForExit();
            pro.Close();
            return output;
        }

        private static int fileIndex = 0;

        public static string SaveFileListPublic(List<string> files, string name) => SaveFileList(files, name);

        /// <summary>
        /// 查询文件列表中被他人锁定的文件。
        /// 只读查询，不执行 lock 操作。
        /// </summary>
        /// <param name="fileList">待查询文件列表（本地绝对路径）</param>
        /// <param name="callback">回调：key=本地路径，value=锁定者用户名</param>
        /// <param name="timeOut">超时（ms），-1 = 不限</param>
        public static void SyncGetLockedFileMap(List<string> fileList, Action<Dictionary<string, string>> callback, int timeOut = -1)
        {
            var lockedMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

            SyncCallP4("fstatFiles", result =>
            {
                if (!result.Contains("Error") && !string.IsNullOrEmpty(result))
                {
                    try
                    {
                        JsonData json = JsonMapper.ToObject(result);
                        for (int i = 0; i < json.Count; i++)
                        {
                            var obj = json[i];
                            if (obj.IsString) continue;
                            if (!obj.Keys.Contains("clientFile")) continue;

                            var clientFile = obj["clientFile"].ToString().Replace("\\", "/");
                            if (!obj.Keys.Contains("otherLock")) continue;

                            string lockerName = "";
                            foreach (var locker in obj["otherLock"])
                            {
                                if (locker != null && !string.IsNullOrEmpty(locker.ToString()))
                                    lockerName = locker.ToString();
                            }
                            lockedMap[clientFile] = lockerName;
                        }
                    }
                    catch (System.Exception ex)
                    {
                        UnityEngine.Debug.LogWarning($"[P4Utils] SyncGetLockedFileMap 解析失败: {ex.Message}");
                    }
                }
                callback?.Invoke(lockedMap);
            }, filePath: SaveFileList(fileList, "LockCheck"), timeOut: timeOut);
        }

        private static string SaveFileList(List<string> files, string name)
        {
            var content = string.Join(',', files).Replace("\\","/");
            var path = Application.dataPath.Replace("Assets", $"Cache{name}_{fileIndex++}.txt");
            if (!File.Exists(path))
            {
                File.Create(path).Dispose();
            }

            //EditorCommonLogger.LogInfo($"{name} 文件列表：{content}");
            if (Environment.OSVersion.Platform == PlatformID.MacOSX ||
                Environment.OSVersion.Platform == PlatformID.Unix)
            {
                foreach (var item in MacPathReplaceDict)
                {
                    content = content.Replace(item.Key, item.Value);
                }
            }
            File.WriteAllText(path, content, Encoding.GetEncoding("GBK"));
            return path;
        }
        
        public static void Fix()
        {
            ProcessStartInfo processInfo = new ProcessStartInfo();
            processInfo.UseShellExecute = true;
            processInfo.FileName = $"{GetP4ToolDirPath()}\\FixP4.bat";
            processInfo.Arguments = $"{GetPythonExePath("pip.exe")}";
            var start = Process.Start(processInfo);
            start.WaitForExit();
            EditorUtility.DisplayDialog("提示", "修复成功！请重试", "OK");
        }

        public static bool IsArtistStream()
        {
            return IsSymbolicLink(Path.Combine(Application.dataPath, "Scripts"));
        }

        public static bool IsSymbolicLink(string path)
        {
            if (!Directory.Exists(path))
            {
                return false; // 路径不存在或不是一个目录
            }

            var pathInfo = new FileInfo(path);
            return (pathInfo.Attributes & FileAttributes.ReparsePoint) == FileAttributes.ReparsePoint;
        }
    }
}
