using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using EditorCommon.Editor;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace EditorCommon
{
    public enum EState
    {
        Updating = 0,
        UpdateFail,
        UpdateSuc,
        GetChangeFileing,
        GetChangeFileSuc,
        GetChangeFileClean,
        GetChangeFileFail,
        Committing,
        CommitFail,
        CommitFailShowed,
        CommitSuc,
        CommitSucPostCheck,
        CommitClean,
        RevertFail,
        RevertSuc,
    }
    
    public enum CommitMode
    {
        Directory,
        FileList,
    }
    public class Commiter
    {
        public EState State = EState.Updating;
        public string[] dir;
        public Action<List<ChangeFileInfo>> OnGetChangeFileEnd;

        public bool revert;
        /// <summary>
        /// 提交来源  用于编辑器窗口中显示
        /// </summary>
        public string name;

        public string excloud = "";

        /// <summary>
        /// 当前的commit模式
        /// </summary>
        public CommitMode CurrentMode = CommitMode.Directory;

        private List<UpdateFailFile> updateFailFiles = new List<UpdateFailFile>();
        public List<ChangeFileInfo> changeFileInfos = new List<ChangeFileInfo>();

        public Dictionary<string, List<ChangeFileInfo>> _showChangeInfos;
        Dictionary<string, bool> showChangeInfosFolders = new();

        public Dictionary<string, List<ChangeFileInfo>> showChangeInfos
        {
            get
            {
                if (_showChangeInfos == null || _showChangeInfos.Count <= 0)
                {
                    _showChangeInfos = new();
                    showChangeInfosFolders = new();
                    changeFileInfos.Sort((t1, t2) => t1.ext.CompareTo(t2.ext));
                    foreach (var file in changeFileInfos)
                    {
                        var key = string.IsNullOrEmpty(file.ext) ? "" : file.ext;
                        if (!_showChangeInfos.ContainsKey(key))
                        {
                            _showChangeInfos.Add(key, new List<ChangeFileInfo>());
                            showChangeInfosFolders.Add(key, true);
                        }

                        _showChangeInfos[key].Add(file);
                    }
                }

                return _showChangeInfos;
            }
        }

        private Vector2 sc;

        public void TryUpdata()
        {
            updateFailFiles ??= new();
            updateFailFiles.Clear();
            if (CurrentMode == CommitMode.Directory)
            {
                State = EState.Updating;
                foreach (var dir_ in dir)
                {
                    P4Utils.Update(dir_, OnUpdateEnd,false);
                }
                GetLocalChangeFiles();
            }
            else
            {
                P4Utils.CheckFileListEditState(changeFileInfos,
                    (bok, fileInfoList) =>
                    {
                        if (bok)
                        {
                            State = EState.UpdateSuc;
                            changeFileInfos = fileInfoList;
                            _showChangeInfos = null;
                            OnGetChangeFileEnd?.Invoke(changeFileInfos);
                            if (changeFileInfos == null || changeFileInfos.Count <= 0)
                            {
                                State = EState.GetChangeFileClean;
                            }
                            else
                            {
                                State = EState.GetChangeFileSuc;
                            }
                        }
                        else
                        {
                            State = EState.GetChangeFileFail;
                        }
                    });
            }
        }

        private void OnUpdateEnd(bool bOk, List<UpdateFailFile> list)
        {
            if (!bOk)
            {
                State = EState.UpdateFail;
            }

            State = EState.UpdateSuc;
            updateFailFiles.AddRange(list);
        }

        private void GetLocalChangeFiles()
        {
            changeFileInfos.Clear();
            State = EState.GetChangeFileing;
            bool isSuccess_ = true;
            foreach(var dir_ in dir)
            {
                P4Utils.GetDirChangeFiles(dir_, (bok, changeFileInfos) =>
                {
                    if (bok)
                    {
                        this.changeFileInfos.AddRange(changeFileInfos);
                    }
                    else
                    {
                        isSuccess_ = isSuccess_ && bok;
                    }
                },false);
            }
            OnGetChangeFileEnd?.Invoke(this.changeFileInfos);
            if (isSuccess_)
            {
                State = EState.GetChangeFileSuc;
                if (changeFileInfos == null || changeFileInfos.Count <= 0)
                {
                    State = EState.GetChangeFileClean;
                }
            }
            else
            {
                State = EState.GetChangeFileFail;
            }
        }

        public void DrawSelf()
        {
            if (State == EState.GetChangeFileClean)
            {
                WXLayoutUtils.DrawLabelSize(name + "没有改动文件", 15);
            }
            else
            {
                sc = EditorGUILayout.BeginScrollView(sc);
                DrawChangeFiles();
                EditorGUILayout.EndScrollView();
            }
        }

        private void DrawChangeFiles()
        {
            var r1 = GUI.skin.toggle.richText;
            var r2 = EditorStyles.foldout.richText;
            GUI.skin.toggle.richText = true;
            EditorStyles.foldout.richText = true;
            DrawChangeFiles("新增列表", "add");
            GUILayout.Space(5);
            DrawChangeFiles("修改列表", "edit");
            GUILayout.Space(5);
            DrawChangeFiles("删除列表", "delete");
            EditorStyles.foldout.richText = r2;
            GUI.skin.toggle.richText = r1;
        }

        Color selectColor = new Color(0.156f, 0.936f, 0.922f, 0.8f);

        private GUIStyle foldoutStyle;
        private GUIContent foldoutContent = new GUIContent();
        private float textMaxWidth = 0;
        private Dictionary<string, int> handleFlags = new();
        private void DrawChangeFiles(string text, string action)
        {
            foldoutStyle ??= EditorStyles.foldout;
            handleFlags.Clear();
            if (WXLayoutUtils.DrawHeader(text, action + "_P4Commit", true, false))
            {
                using (new GUILayout.VerticalScope("helpbox"))
                {
                    using (new GUILayout.HorizontalScope())
                    {
                        DrawFunc((handleFlag) =>
                        {
                            foreach (var item in showChangeInfos)
                                handleFlags.Add(item.Key,handleFlag);
                        });
                    }

                    foreach (var item in showChangeInfos)
                    {
                        bool show = false;
                        var changeFileInfos = item.Value;
                        foreach (var file in changeFileInfos)
                        {
                            if (!string.IsNullOrEmpty(excloud) && file.clientFile.Contains(excloud)) continue;
                            if (file.action == null || !file.action.Contains(action)) continue;
                            show = true;
                        }

                        if (!show) continue;
                        var FoldoutKey = $"{item.Key}_{action}";
                        if (!showChangeInfosFolders.ContainsKey(FoldoutKey))
                        {
                            showChangeInfosFolders.Add(FoldoutKey, true);
                        }

                        bool needRetract = false;
                        if (!string.IsNullOrEmpty(item.Key))
                        {
                            using (new GUILayout.HorizontalScope())
                            {
                                foldoutContent.text = $"<size=13><color=#2FD708>{item.Key}</color></size>";
                                float width = foldoutStyle.CalcSize(foldoutContent).x;
                                if (width > textMaxWidth)
                                    textMaxWidth = width;

                                showChangeInfosFolders[FoldoutKey] = EditorGUILayout.Foldout(
                                    showChangeInfosFolders[FoldoutKey],
                                    foldoutContent);
                                GUILayout.Space(textMaxWidth - 50);
                                DrawFunc((handleFlag) => { handleFlags[item.Key] = handleFlag; });
                                GUILayout.FlexibleSpace();
                                needRetract = true;

                            }
                        }

                        if (!showChangeInfosFolders[FoldoutKey]) continue;
                        foreach (var file in changeFileInfos)
                        {
                            bool needMerge = false;
                            if (!string.IsNullOrEmpty(excloud) && file.clientFile.Contains(excloud)) continue;
                            if (file.action == null || !file.action.Contains(action)) continue;
                            int handleFlag = -1;
                            if (handleFlags.TryGetValue(item.Key, out var flag))
                                handleFlag = flag;
                            if (handleFlag != -1)
                            {
                                file.select = handleFlag == 0 || (handleFlag != 1 && !file.select);
                            }

                            if (updateFailFiles.FindIndex(t => { return t.file == file.clientFile; }) >= 0)
                            {
                                needMerge = true;
                                if (!revert)
                                {
                                    GUI.enabled = false;
                                    file.select = false;    
                                }
                            }

                            using (new GUILayout.HorizontalScope())
                            {
                                if (needRetract) GUILayout.Space(15f);
                                if (action == "edit" && GUILayout.Button("Diff", GUILayout.Width(35)))
                                {
                                    P4Utils.ShowDiff(file);
                                }

                                string tips = revert ? "请注意,该文件有冲突" : "该文件有冲突,请到P4中处理";
                                var content = $"{file.clientFile}{(!needMerge ? "" : tips)}";
                                file.select = GUILayout.Toggle(file.select,content);
                                GUILayout.FlexibleSpace();
                                if (GUILayout.Button(new GUIContent("CopyPath", "点击可复制对应路径，粘贴到P4V的地址栏可以定位到对应文件") , GUILayout.Width(70)))
                                {
                                    GUIUtility.systemCopyBuffer = file.clientFile;
                                }

                                bool state = GUI.enabled;
                                GUI.enabled = true;
                                if (GUILayout.Button(new GUIContent("Show in Explorer")))
                                {
                                    MouseRightClick(file.clientFile);
                                }

                                GUI.enabled = state;
                            }

                            GUI.enabled = true;
                        }
                    }
                }
            }
        }

        private void MouseRightClick(string path)
        {
            if (Path.HasExtension(path))
            {
                try
                {
                    if (File.Exists(path))
                    {
                        string windowsPath = path.Replace("/", "\\");
                        Process.Start("explorer.exe", $"/select,\"{windowsPath}\"");
                    }
                    else
                    {
                        FileInfo info = new FileInfo(path);
                        Application.OpenURL(info.Directory.FullName);
                    }
                   
                }
                catch (Exception e)
                {
                    FileInfo info = new FileInfo(path);
                    Application.OpenURL(info.Directory.FullName);
                }
            }
            else
            {
                Application.OpenURL(path);
            }
        }

        public void DrawFunc(Action<int> clickAction = null)
        {
            if (GUILayout.Button("全选", GUILayout.Width(50)))
            {
                clickAction?.Invoke(0);
            }

            if (GUILayout.Button("全不选", GUILayout.Width(50)))
            {
                clickAction?.Invoke(1);
            }

            if (GUILayout.Button("反选", GUILayout.Width(50)))
            {
                clickAction?.Invoke(2);
            }
        }

        public void GetCommitFiles(List<string> list)
        {
            bool isSelect = false;
            var allFile = new List<string>();
            foreach (var file in changeFileInfos)
            {
                allFile.Add($"{file.clientFile} [{file.action}]  [{file.select}]");
                if (file.select)
                {
                    list.Add(file.clientFile);
                    isSelect = true;
                }
            }
            
            if (isSelect)
            {
                State = EState.Committing;
            }

            EditorCommonLogger.LogInfo(
                $"【{name}】改动数据情况\n{string.Join('\n', allFile)})\n----");
        }

        public string commitTriggerError = "";

        public void Revert()
        {
            var list = new List<string>();
            var allFile = new List<string>();
            foreach (var file in changeFileInfos)
            {
                allFile.Add(file.clientFile);
                if (file.select)
                {
                    list.Add(file.clientFile);
                }
            }

            if (list.Count > 0)
            {
                State = EState.Committing;
                P4Utils.SyncRevertFiles(list, (b =>
                {
                    State = b ? EState.RevertSuc : EState.RevertFail;
                    if (b)
                    {
                        PostCommitOrRevertCheck(false);
                        var revertedSet_ = new HashSet<string>(list);
                        for(int i = 0; i < changeFileInfos.Count; i++)
                        {
                            if (revertedSet_.Contains(changeFileInfos[i].clientFile))
                            {
                                changeFileInfos.RemoveAt(i);
                                i--;
                            }
                        }
                        if (_showChangeInfos != null)
                        {
                            foreach (var showItem_ in _showChangeInfos.Where(showItem_ => showItem_.Value != null))
                            {
                                for(int i = 0; i < showItem_.Value.Count; i++)
                                {
                                    if (revertedSet_.Contains(showItem_.Value[i].clientFile))
                                    {
                                        showItem_.Value.RemoveAt(i);
                                        i--;
                                    }
                                }
                            }
                        }
                    }
                }));
            }
            Debug.Log(
                $"【{name}】 开始回退!\n 待回退的文件\n:{string.Join('\n', allFile)}\n 选中的文件\n：{string.Join('\n', list)}\n----");
        }
        
        public void PostCommitOrRevertCheck(bool commitFlg = true)
        {
            switch (CurrentMode)
            {
                case CommitMode.Directory:
                    State = commitFlg ? EState.CommitSucPostCheck : EState.RevertSuc;
                    break;
                case CommitMode.FileList:
                    State = commitFlg ? EState.CommitSucPostCheck : EState.RevertSuc;
                    break;
            }
        }
    }
}