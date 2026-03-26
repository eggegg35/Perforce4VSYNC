using System;
using System.Collections.Generic;
using EditorCommon.Editor;
using UnityEditor;
using UnityEngine;

namespace EditorCommon
{
    public class SelectPendlingListPopup : PopupWindowContent
    {
        public List<ChangeListInfo> changeListInfos = new();
        public List<string> showNames = new();

        private Action<ChangeListInfo> OnSelect;
        Vector2 sc;
        string curSelect;
        int selectIndex;

        public override Vector2 GetWindowSize()
        {
            return new Vector2(500, Math.Min(changeListInfos.Count * 20 + 100f, 750));
        }

        public static void Open(Action<ChangeListInfo> OnSelect)
        {
            var popup = new SelectPendlingListPopup();
            popup.OnSelect = OnSelect;
            Rect rect = new Rect();
            rect = Event.current is not null ? 
                new Rect(Event.current.mousePosition.x, Event.current.mousePosition.y, 0, 0) : 
                new Rect(Screen.width/2, Screen.height/2, 0, 0);
            PopupWindow.Show(rect, popup);
        }

        public override void OnOpen()
        {
            base.OnOpen();
            changeListInfos = new();
            changeListInfos.Add(new ChangeListInfo() { changeId = "default", desc = "" });
            showNames.Add("default");
            changeListInfos.Add(new ChangeListInfo() { changeId = "New", desc = "" });
            showNames.Add("New 新建一个ChangeList");
            P4Utils.SyncGetLocalChangelist((bok, infos) =>
            {
                foreach (var i in infos)
                {
                    changeListInfos.Add(i);
                    showNames.Add($"{i.changeId}   {i.desc.Replace("\n", " ")}");
                }
            });
        }

        public override void OnGUI(Rect rect)
        {
            WXLayoutUtils.DrawLabelSize("选择一个ChangeList", 13);
            WXLayoutUtils.Separator();
            WXLayoutUtils.DrawSearchableList(showNames, ref curSelect, ref selectIndex, ref sc, null, 495);
            using (new GUILayout.HorizontalScope())
            {
                GUILayout.FlexibleSpace();
                if (GUILayout.Button("确认", GUILayout.Height(25), GUILayout.Width(80)))
                {
                    OnSelect?.Invoke(changeListInfos[selectIndex]);
                }

                if (GUILayout.Button("取消", GUILayout.Height(25), GUILayout.Width(80)))
                {
                    editorWindow?.Close();
                }

                GUILayout.FlexibleSpace();
            }

            editorWindow?.Repaint();
        }
    }
}