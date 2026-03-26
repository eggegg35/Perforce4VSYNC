using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using EditorCommon.Editor.Res;
using Sirenix.OdinInspector;
using Sirenix.OdinInspector.Editor;
using UnityEngine;
using UnityEditor;
using Object = UnityEngine.Object;

namespace EditorCommon
{
    public class SimpleP4CommitWindow : OdinEditorWindow
    {
        [MenuItem("Assets/P4/快捷提交 %&T", false, 16)]
        public static void Open()
        {
            var wnd = GetWindow<SimpleP4CommitWindow>();
            wnd.titleContent = new GUIContent("P4便捷提交窗口");
            foreach (var obj in Selection.GetFiltered(typeof(UnityEngine.Object), SelectionMode.Assets))
            {
                if (wnd.commitList.Contains(obj)) continue;
                wnd.commitList.Add(obj);
            }
        }

        [TitleGroup("提交信息")] [TextArea(4, 10)] [HideLabel]
        public string commitMsg = "";

        [LabelText("待提交列表")] public List<Object> commitList = new List<Object>();

        [Button("提交", ButtonSizes.Large)]
        [PropertySpace(10)]
        public void Commit()
        {
            if (commitList.Count == 0)
            {
                EditorUtility.DisplayDialog("提示", "请选择要提交的资源", "确定");
                return;
            }

            if (string.IsNullOrEmpty(commitMsg))
            {
                EditorUtility.DisplayDialog("提示", "请填入提交单子信息", "确定");
            }

            var absBase = Directory.GetParent(Application.dataPath)?.FullName;
            var pathList = new List<string>();
            foreach (var obj in commitList)
            {
                if (obj == null) continue;
                var path = AssetDatabase.GetAssetPath(obj);
                var absPath = CommonAssetManager.GetRealPath(Path.Combine(absBase, path).Replace("/", "\\"));
                var absPathMeta = absPath + ".meta";
                pathList.Add(absPath);
                pathList.Add(absPathMeta);
            }

            P4Utils.CommitFiles(pathList, commitMsg, OnCommit);
        }

        public void OnCommit(bool bOk, string arg)
        {
            if (bOk)
            {
                EditorUtility.DisplayDialog("提示", $"提交成功!", "确定");
                Close();
            }
            else
            {
                var forceClose = false;
                var commitTriggerError = "";
                string key = "---------------------[P4-Trigger ERROR]--------------------";
                string pattern = @" 'p4 submit -c ([\s\S]*?)'";
                Match match = Regex.Match(arg, pattern);
                var changeListID = "";
                if (match.Success)
                {
                    changeListID = match.Groups[1].Value;
                }

                if (arg.Contains(key))
                {
                    arg = arg.Replace(key, "#@#");
                    commitTriggerError = arg.Split("#@#")[1].Replace("\n", " ");
                }

                if (arg.Contains("[change_content_trigger] description should contain --story=id --user=name msg"))
                {
                    commitTriggerError = "提交单子不合法！请填入你需要提交的单子信息！";
                }

                if (arg.Contains("飞书单子信息") || arg.Contains("Tapd单子信息"))
                {
                    commitTriggerError = "提交单子不合法！请填入能够合法提交的单子信息！";
                }

                if (arg.Contains("请先生成review"))
                {
                    commitTriggerError =
                        $"你的此次提交需要review！请到P4V中操作！\n【{name}】待提交的内容已经放入\nChanggeList:【{changeListID}】中。";
                    forceClose = true;
                }

                if (arg.Contains("WorldX_Submit"))
                {
                    commitTriggerError =
                        $"你的此次提交需要使用P4工具WorldX_Submit提交！请到P4V中操作！\n【{name}】待提交的内容已经放入\nChanggeList:【{changeListID}】中。";
                    forceClose = true;
                }

                if (EditorUtility.DisplayDialog("提示",
                        string.IsNullOrEmpty(commitTriggerError) ? $"提交失败!\n{arg}" : $"提交失败!\n{commitTriggerError}",
                        "确认并关闭提交窗口", "检查一下"))
                {
                    forceClose = true;
                }

                if (forceClose) Close();
            }
        }
    }
}