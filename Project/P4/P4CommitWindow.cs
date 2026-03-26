using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using EditorCommon.Editor;
using System;
using System.IO;
using System.Text.RegularExpressions;
using LitJson;
using Path = System.IO.Path;

namespace EditorCommon
{
    public delegate bool PreCommitHook(List<ChangeFileInfo> changeFileInfos);
    public class P4CommitWindow : EditorWindow
    {
        public PreCommitHook preCommitHook;
        public Action<List<string>> PostCommitHook;
        public Action PostRevertHook;

        public List<Commiter> commiters = new List<Commiter>();
        public GUIContent[] tabs = new GUIContent[4];
        public int index = 0;

        public CommitMode CurrentMode = CommitMode.Directory;

        // 切至revert模式，不显示提交窗口
        public bool revert;
        // 切至全功能模式，支持提交和回退
        public bool fullFunc;

        public static void CommitDir(string name, string dirPath, PreCommitHook preCommit = null, bool revert = false,Action postRevertHook = null)
        {
            CommitDir(new Dictionary<string, string> { { name, dirPath } }, preCommit, revert,null,postRevertHook);
        }

        public static void CommitDir(Dictionary<string, string> dirPaths, PreCommitHook preCommit = null,
            bool revert = false, Action<List<Commiter>> OnCommiterCreated = null,Action postRevertHook = null, bool fullFunc = false)
        {
            var w = GetWindow<P4CommitWindow>();
            w.minSize = new Vector2(900, 600);
            w.titleContent = new GUIContent("P4 提交界面");
            w.commiters.Clear();
            w.tabs = new GUIContent[dirPaths.Count];
            w.revert = revert;
            w.fullFunc = fullFunc;
            int i = 0;
            foreach (var item in dirPaths)
            {
                var key = item.Key;
                var excloud = "";
                if (key.Contains("|"))
                {
                    var info = key.Split('|');
                    key = info[0];
                    excloud = info[1];
                }

                var c = new Commiter()
                {
                    dir = GetDirList(item.Value),
                    name = key,
                    excloud = excloud,
                    revert = revert,
                };
                w.commiters.Add(c);
                w.tabs[i++] = new GUIContent(key, item.Value);
            }

            w.preCommitHook = preCommit;
            w.PostRevertHook = postRevertHook;
            OnCommiterCreated?.Invoke(w.commiters);
            w.TryUpdata();
        }

        /// <summary>
        /// 传入一个Filelist提交，注意目前项目的要求，.meta文件记得一起传进来！
        /// </summary>
        /// <param name="assetList"></param>
        /// <param name="preCommit"></param>
        public static void CommitAssetList(List<string> assetList, PreCommitHook preCommit = null,
            Action<List<string>> closeHook = null, bool revert = false, Action<List<Commiter>> OnCommiterCreated = null)
        {
            var w = GetWindow<P4CommitWindow>();
            w.minSize = new Vector2(900, 600);
            w.titleContent = new GUIContent("P4 提交界面");
            w.commiters.Clear();
            w.CurrentMode = CommitMode.FileList;
            w.tabs = new GUIContent[1]{new GUIContent()};
            w.revert = revert;
            int i = 0;
            var c = new Commiter()
            {
                dir = null,
                name = "List数据",
                CurrentMode = CommitMode.FileList,
                revert = revert,
            };
            w.commiters.Add(c);
            w.tabs[0] = new GUIContent("AssetData", "");
            foreach (var item in assetList)
            {
                ChangeFileInfo changeFileInfo = new ChangeFileInfo();
                changeFileInfo.clientFile = item;
                c.changeFileInfos.Add(changeFileInfo);
            }
            w.preCommitHook = preCommit;
            w.PostCommitHook = closeHook;
            OnCommiterCreated?.Invoke(w.commiters);
            w.TryUpdata();
        }

        public static void CommitDirAndAssetList(Dictionary<string, string> dirPaths, PreCommitHook precommit = null,
            Action<List<string>> closeHook = null, bool revert = false, Action<List<Commiter>> OnCommiterCreated = null, bool fullFunc = false)
        {
            var w = GetWindow<P4CommitWindow>();
            w.minSize = new Vector2(900, 600);
            w.titleContent = new GUIContent("P4 提交界面");
            w.commiters.Clear();
            w.preCommitHook = precommit;
            w.PostCommitHook = closeHook;
            w.revert = revert;
            w.fullFunc = fullFunc;
            List<GUIContent> pathTab = new List<GUIContent>();
            List<string> assetList = new List<string>();
            foreach (var item in dirPaths)
            {
                var key = item.Key;
                if (!string.IsNullOrEmpty( Path.GetExtension(item.Value)))
                {
                    assetList.Add(item.Value);
                    continue;
                }
                
                var excloud = "";
                if (key.Contains("|"))
                {
                    var info = key.Split('|');
                    key = info[0];
                    excloud = info[1];
                }
                var dir_c = new Commiter()
                {
                    dir = GetDirList(item.Value),
                    name = key,
                    excloud = excloud,
                    CurrentMode = CommitMode.Directory,
                    revert = revert,
                };
                
                w.commiters.Add(dir_c);
                pathTab.Add(new GUIContent(key, item.Value));
            }
            
            if (assetList.Count > 0)
            {
                var files_c = new Commiter()
                {
                    dir = null,
                    name = "List数据",
                    CurrentMode = CommitMode.FileList,
                    revert = revert,
                };
                foreach (var item in assetList)
                {
                    ChangeFileInfo changeFileInfo = new ChangeFileInfo();
                    changeFileInfo.clientFile = item;
                    files_c.changeFileInfos.Add(changeFileInfo);
                }

                pathTab.Add(new GUIContent("AssetData", ""));
                w.commiters.Add(files_c);   
            }
            
            w.tabs = pathTab.ToArray();
            OnCommiterCreated?.Invoke(w.commiters);
            w.TryUpdata();
        }

        /// <summary>
        /// 根据分隔符得到路径列表
        /// </summary>
        /// <param name="_dirStr"></param>
        /// <returns></returns>
        private static string[] GetDirList(string _dirStr)
        {
            if (_dirStr == null)
                return Array.Empty<string>();
            return _dirStr.Split('|');
        }

        private static string GetDirListShow(string[] _dirList)
        {
            if (_dirList == null || _dirList.Length == 0)
                return string.Empty;
            string display_ = _dirList[0];
            for(int i = 1; i < _dirList.Length; i++)
            {
                display_ += '\n' + _dirList[i];
            }
            return display_;
        }

        private Vector2 pos;
        
        private void GetTabShowCount()
        {
            var index = 0;
            foreach (var c in commiters)
            {
                var allFileCount = c.changeFileInfos.Count;
                var selectFileCount = c.changeFileInfos.FindAll(t => t.select).Count;
                tabs[index++] = new GUIContent($"{c.name}({selectFileCount}/{allFileCount})", GetDirListShow(c.dir));
            }
        }

        private void TryUpdata()
        {
            foreach (var c in commiters)
            {
                c.TryUpdata();
            }
        }

        string msg = "";
        
        public void OnGUI()
        {
            if (EditorApplication.isCompiling)
            {
                Close();
            }

            GetTabShowCount();
            WXLayoutUtils.DrawTitle(revert ? "P4 回退" : "P4 提交");
            WXLayoutUtils.Separator();
            if (GUILayout.Button("Recent messages", GUILayout.Width(120)))
            {
                if (recentMsg is not { Count: > 0 })
                {
                    EditorUtility.DisplayDialog("提示", "本地没有提交记录", "OK");
                }
                else
                {
                    SelectStringPopup.Open(Event.current.mousePosition, 900, recentMsg, null, null, null,
                        (index, str) => { msg = str; });
                }
            }
            GUILayout.Label("填入提交单子信息后再提交");
            msg = EditorGUILayout.TextArea(msg, GUILayout.Height(60));
            {
                GUILayout.Space(5);
                pos = GUILayout.BeginScrollView(pos);
                using (new GUILayout.HorizontalScope())
                {
                    GUILayout.Space(1);
                    index = GUILayout.Toolbar(index, tabs, GUILayout.Height(30));
                    GUILayout.FlexibleSpace();
                    GUILayout.Space(1);
                }

                GUILayout.EndScrollView();
                try
                {
                    commiters[index].DrawSelf();
                    Repaint();
                }
                catch
                {
                }
            }
            GUILayout.FlexibleSpace();
            DrawBtns();
            GUILayout.Space(3);
            WXLayoutUtils.Separator();
            if (commiters.Count > 0)
                DrawState(commiters[index]);
        }

        public void DrawBtns()
        {
            using (new GUILayout.HorizontalScope())
            {
                GUILayout.FlexibleSpace();
                var enable = GUI.enabled;
                GUI.enabled = !(IsState(EState.Committing) || IsState(EState.GetChangeFileing));
                if (!revert && !string.IsNullOrEmpty(msg) &&
                    GUILayout.Button("提 交", GUILayout.Height(30), GUILayout.Width(120)))
                {
                    EditorUtility.DisplayDialog("提示", "Unity内提交会拉起多分支提交工具进行实际提交哈，此提示会在一周后关掉。", "好的");
                    AddRecent(msg);
                    var changeFileInfos = new List<ChangeFileInfo>();
                    foreach (var c in commiters)
                    {
                        changeFileInfos.AddRange(c.changeFileInfos);
                    }

                    if (preCommitHook == null || (preCommitHook != null && preCommitHook.Invoke(changeFileInfos)))
                    {
                        var list = new List<string>();
                        EditorCommonLogger.LogInfo("开始提交");
                        foreach (var c in commiters)
                        {
                            c.GetCommitFiles(list);
                        }

                        P4Utils.CallBranchCommitFiles(list, msg, OnCommit);
                    }
                }
                GUI.enabled = enable;
                if ((fullFunc || revert) && GUILayout.Button("回 退", GUILayout.Height(30), GUILayout.Width(120)))
                {
                    foreach (var c in commiters)
                    {
                        c.Revert();
                    }
                }
                if (GUILayout.Button("取消", GUILayout.Height(30), GUILayout.Width(120)))
                {
                    Close();
                }

                if (!revert && GUILayout.Button("加入pengding list(暂不提交)",
                        GUILayout.Height(30), GUILayout.Width(220)))
                {
                    var list = new List<string>();
                    EditorCommonLogger.LogInfo("加入pengding list(暂不提交)");
                    foreach (var c in commiters)
                    {
                        c.GetCommitFiles(list);
                    }

                    SelectPendlingListPopup.Open(info =>
                    {
                        P4Utils.FilesAddToPendingList(list, info.changeId,
                            string.IsNullOrEmpty(msg) ? "Unity内P4通用提交自动创建" : msg, (bok, ret) =>
                            {
                                if (bok)
                                {
                                    ret = ret.Replace(" ", "");
                                    var tips = ret == "NoChangeId"
                                        ? "没有任何文件添加到PendlingList"
                                        : $"添加到PendlingList成功! 请查看Id为【{ret}】的ChangeList";
                                    EditorUtility.DisplayDialog("提示", tips,
                                        "Ok");
                                    Close();
                                }
                                else
                                    EditorUtility.DisplayDialog("提示", "添加到PendingList失败！", "Ok");
                            });
                    });
                }

                GUILayout.FlexibleSpace();
            }
        }

        public void DrawState(Commiter c)
        {
            switch (c.State)
            {
                case EState.Updating:
                    GUILayout.Label(c.name + ":  正在更新...，更新成功后会刷新文件列表！");
                    break;
                case EState.UpdateFail:
                    GUILayout.Label(c.name + ":  更新失败！估计P4抽风了...找开发看一下");
                    break;
                case EState.UpdateSuc:
                    GUILayout.Label(c.name + ":  更新成功！");
                    break;
                case EState.GetChangeFileing:
                    GUILayout.Label(c.name + ":  正在获取本地改动文件列表...");
                    break;
                case EState.GetChangeFileSuc:
                    GUILayout.Label(c.name + ":  获取本地改动文件列表结束");
                    break;
                case EState.GetChangeFileFail:
                    GUILayout.Label(c.name + ":  获取本地改动文件列表失败。找开发看一下");
                    break;
                case EState.CommitFail:
                case EState.CommitFailShowed:
                    GUILayout.Label(c.name + ":  提交失败了！！！请查看日志详细信息");
                    break;
                case EState.CommitSuc:
                case EState.CommitSucPostCheck:
                    GUILayout.Label(c.name + ":  提交成功！");
                    break;
                case EState.Committing:
                    GUILayout.Label(c.name + ":  正在提交...别着急！最近P4提交很慢，提交成功后会有弹窗提示。");
                    break;
                case EState.RevertFail:
                    GUILayout.Label(c.name + ":  Revert 失败");
                    break;
                case EState.RevertSuc:
                    GUILayout.Label(c.name + ":  Revert 成功");
                    break;
            }
        }

        public void CheckState()
        {
            CheckState(EState.UpdateFail, "更新失败", EState.Updating);
            CheckState(EState.GetChangeFileFail, "Reconcile失败", EState.GetChangeFileing);
            CheckClean(EState.GetChangeFileClean, "提交目录中没有改动文件");
            //CheckClean(EState.CommitClean, "");
            CheckClean(EState.CommitSucPostCheck, "");
            //CheckClean(EState.RevertSuc, "Revert成功！");
            CheckCommit();
        }

        public void CheckState(EState state, string errorType, EState checkState)
        {
            if (commiters.Count <= 0) return;
            if (IsState(checkState)) return;
            bool allFail = true;
            string errorInfo = "";
            for (int i = commiters.Count - 1; i >= 0; --i)
            {
                if (commiters[i].State == state)
                {
                    errorInfo += $"{commiters[i].name}{errorType}！\n";
                    commiters.RemoveAt(i);
                }
                else
                {
                    allFail = false;
                }
            }

            if (!string.IsNullOrEmpty(errorInfo))
            {
                if (allFail)
                {
                    if (EditorUtility.DisplayDialog("提示",
                            $"提交目录{errorType}，提交流程终止！（请到Window/P4/设置P4信息,确认已经正确配置，再重新提交）",
                            "好的"))
                    {
                        //P4Utils.Fix();
                    }
                    Close();
                    return;
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", $"{errorInfo} 以上目录{errorType}！移出提交界面。", "好的");
                }
            }

            ResetTab();
        }

        public void CheckClean(EState state, string tips)
        {
            if (commiters.Count <= 0) return;
            bool cleanFlag = true;
            for (int i = commiters.Count - 1; i >= 0; --i)
            {
                if (commiters[i].State == state)
                {
                    commiters.RemoveAt(i);
                }
                else
                {
                    cleanFlag = false;
                }
            }

            if (cleanFlag)
            {
                if (!string.IsNullOrEmpty(tips)) EditorUtility.DisplayDialog("提示", $"{tips}!", "好的");
                PostRevertHook?.Invoke();
                Close();
                return;
            }
            else ResetTab();
        }

        public bool IsState(EState state)
        {
            bool committing = false;
            for (int i = commiters.Count - 1; i >= 0; --i)
            {
                if (commiters[i].State == state)
                {
                    committing = true;
                    break;
                }
            }

            return committing;
        }

        public void CheckCommit()
        {
            if (commiters.Count <= 0) return;
            if (IsState(EState.Committing)) return;
            var commitSucStr = "";
            var commitFailStr = "";
            for (int i = commiters.Count - 1; i >= 0; --i)
            {
                var c = commiters[i];
                if (c.State == EState.CommitSuc)
                {
                    commitSucStr += $"{c.name} 提交成功！\n";
                    if (PostCommitHook != null)
                    {
                        List<string> pathList = new();
                        foreach (var fileInfo in c.changeFileInfos)
                        {
                            pathList.Add(fileInfo.clientFile);
                        }

                        PostCommitHook.Invoke(pathList);
                    }

                    c.PostCommitOrRevertCheck();
                }

                if (c.State == EState.CommitFail)
                {
                    c.State = EState.CommitFailShowed;
                    commitFailStr += $"{c.name} 提交失败！\n";
                    if (!commitFailStr.Contains(c.commitTriggerError))
                    {
                        if (commitFailStr.Contains("你的此次提交需要review！请到P4V中操作！\n"))
                        {
                            c.commitTriggerError = c.commitTriggerError.Replace("你的此次提交需要review！请到P4V中操作！\n", "");
                        }

                        commitFailStr += $"{c.commitTriggerError}\n";
                    }
                }
            }

            if (!string.IsNullOrEmpty(commitSucStr) || !string.IsNullOrEmpty(commitFailStr))
            {
                // if (commitFailStr.Contains("提交需要review"))
                // {
                //     commitFailStr += "\n 如何生成Review请查看文档！";
                //     if (EditorUtility.DisplayDialog("提交结果", $"{commitSucStr}{commitFailStr}", "我要查看文档","老司机了知道怎么review"))
                //     {
                //         Application.OpenURL("https://funplus.feishu.cn/wiki/RVcOwacpNizo8bk7GxHcm1Pkntg");
                //     }
                //     Close();
                // }
                // else
                // {
                //     EditorUtility.DisplayDialog("提交结果", $"{commitSucStr}{commitFailStr}" +
                //                                         $"{(!string.IsNullOrEmpty(commitFailStr) ? "\n有目录提交失败，请查看报错！" : "")}",
                //         "好的");
                // }
            }
        }

        private void OnCommit(bool bOk, string arg)
        {
            if (bOk)
            {
                foreach (var c in commiters)
                {
                    if (c.State == EState.Committing)
                        c.State = EState.CommitSuc;
                }
            }
            else
            {
                var commitTriggerError = "";
                string key = "---------------------[P4-Trigger ERROR]--------------------";
                if (arg.Contains(key))
                {
                    arg = arg.Replace(key, "#@#");
                    commitTriggerError = arg.Split("#@#")[1].Replace("\n"," ");
                }

                if (arg.Contains("[change_content_trigger] description should contain --story=id --user=name msg"))
                {
                    commitTriggerError = "提交单子不合法！请填入你需要提交的单子信息！";
                }

                if (arg.Contains("请先生成review"))
                {
                    string pattern = @" 'p4 submit -c ([\s\S]*?)'";
                    Match match = Regex.Match(arg, pattern);
                    var changeListID = "";
                    if (match.Success)
                    {
                        changeListID = match.Groups[1].Value;
                    }

                    commitTriggerError =
                        $"你的此次提交需要review！请到P4V中操作！\n【{name}】待提交的内容已经放入\nChanggeList:【{changeListID}】中。";
                }
                foreach (var c in commiters)
                {
                    if (c.State == EState.Committing)
                    {
                        c.State = EState.CommitFail;
                        c.commitTriggerError = commitTriggerError;
                    }
                }
            }
        }
        
        public void ResetTab()
        {
            if (tabs.Length != commiters.Count)
            {
                index = 0;
                tabs = new GUIContent[commiters.Count];
                int i = 0;
                foreach (var c in commiters)
                {
                    tabs[i++] = new GUIContent(c.name, GetDirListShow(c.dir));
                }
            }
        }

        public string GetTimeFormat(string time)
        {
            var timestamp = long.Parse(time);
            DateTime offset = new(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
            DateTime dateTime = offset.AddSeconds(timestamp).ToLocalTime();
            return dateTime.ToString("yyyy-MM-dd HH:mm:ss");
        }

        private int MAX_RECENT = 20;
        public void AddRecent(string msg)
        {
            if (recentMsg.Contains(msg))
            {
                recentMsg.Remove(msg);
            }
            recentMsg.Insert(0, msg);
            if (recentMsg.Count > MAX_RECENT)
            {
                recentMsg.RemoveRange(MAX_RECENT,recentMsg.Count - MAX_RECENT);
            }
        }
        
        public List<string> recentMsg = new();

        public void OnEnable()
        {
            bool error = false;
            P4Utils.CheckP4Root((s) =>
            {
                if (s.Contains("Error"))
                {
                    error = true;
                    EditorUtility.DisplayDialog("错误", s, "确定");
                    EditorApplication.delayCall += () => { Close(); };
                }
            });
            if (error) return;
            var recentMsgJsonStr = "";
            if (File.Exists(GetRecentMsgPath()))
            {
                recentMsgJsonStr = File.ReadAllText(GetRecentMsgPath());
            }
            recentMsg = new();
            if (!string.IsNullOrEmpty(recentMsgJsonStr))
            {
                try
                {
                    JsonData jdata = JsonMapper.ToObject(recentMsgJsonStr);
                    var recents = jdata["recents"];
                    for (int i = 0; i < recents.Count; ++i)
                    {
                        recentMsg.Add(recents[i].ToString());
                    }
                }
                catch
                {
                    Debug.Log(recentMsgJsonStr);
                }
            }

            EditorApplication.update -= OnUpdate;
            EditorApplication.update += OnUpdate;
            DataStatisticsUtil.AddDataStatistics("P4CommitWindow");
        }

        public void SaveRecents()
        {
            var recentMsgPath = GetRecentMsgPath();
            JsonData jdata = new JsonData();
            var recents = new JsonData();
            jdata["recents"] = recents;
            if (recentMsg.Count <= 0)
            {
                if (File.Exists(recentMsgPath))
                {
                    File.Delete(recentMsgPath);
                }
            }
            else
            {
                foreach (var r in recentMsg)
                {
                    recents.Add(r);
                }

                if (!File.Exists(recentMsgPath))
                {
                    File.Create(recentMsgPath).Dispose();
                }

                File.WriteAllText(recentMsgPath, jdata.ToJson());
            }
        }
        
        public void OnDestroy()
        {
            EditorApplication.update -= OnUpdate;
        }

        private void OnDisable()
        {
            SaveRecents();
            EditorApplication.update -= OnUpdate;
        }

        private void OnUpdate()
        {
            CheckState();
        }

        private string GetRecentMsgPath()
        {
            return Application.dataPath.Replace("Assets", "P4CommitWindow_recentMsg.json");
        }
    }
}