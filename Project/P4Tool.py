import argparse
import os
import string
import sys
import json
import datetime
import platform
# from LarkTools import LarkTools

try:
    from P4 import P4, P4Exception
except ModuleNotFoundError:
    # log_to_file("P4 module not found. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "p4python"])
    from P4 import P4, P4Exception


def is_mac():
    return platform.system() == "Darwin" and not is_ios()
def is_ios():
    if sys.platform == "ios":
        return True
    if os.path.exists("/Applications") and os.path.exists("/System/Library/CoreServices"):
        return False
    return False

def getP4Client():
    p4 = P4()
    p4.user = args.p4user
    p4.charset = "utf8"
    p4.track = 1
    p4.exception_level = 1
    p4.client = args.p4workspace
    p4.port = "p4-world.funplus.com.cn:1666"
    return p4

def get_p4Path(path: str):
    submitPath = ""
    if is_mac():
        submitPath = path
    else:
        submitPath = os.path.realpath(path)
    if os.path.isdir(path):
        if submitPath[-1] not in ["/", "\\"]:
            submitPath += "/..."
        else:
            submitPath += "..."
    return submitPath

def p4_update(path: str):
    if not path:
        log_to_file("Error:commit 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            # p4.run("revert", "-k", p4Path)
            files = p4.run_sync(p4Path)
            weite_to_log(f"开始更新目录：{path}")
            log_to_file("returnStrStart ")
            for msg in p4.messages:
                log_to_file(msg, "|")
                weite_to_log(f"{msg}")

            log_to_file(" returnStrEnd")
            weite_to_log(f"更新结束：{path}")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_updateF(path: str):
    if not path:
        log_to_file("Error:commit 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            p4.run("revert", "-k", p4Path)
            cleanFiles = p4.run("clean", "-a", "-d", "-e", "-m", p4Path)
            files = p4.run_sync("-f", p4Path)
            log_to_file("returnStrStart ")
            for msg in p4.messages:
                log_to_file(msg, "|")

            log_to_file(" returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_update_f(path: str):
    if not path:
        log_to_file("Error:commit 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            p4.run("revert", p4Path)
            p4.run_sync("-f", p4Path)
            if "..." in p4Path:
                metaPath = p4Path[:-4] + '.meta'
            else:
                metaPath = p4Path + '.meta'
            p4.run("revert", metaPath)
            p4.run_sync("-f", metaPath)
            log_to_file("returnStrStart ")
            for msg in p4.messages:
                log_to_file(msg, "|")

            log_to_file(" returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_UpdateFiles(paths: list):
    if not paths:
        log_to_file("Error:_Update 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            #p4Path = get_p4Path(paths)
            #p4.run("revert", "-k", paths)
            files = p4.run_sync(paths)
            log_to_file("returnStrStart ")
            for msg in p4.messages:
                log_to_file(msg, "|")

            log_to_file(" returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def Get_ResolveFiles_Info(paths: list):
    if not paths:
        log_to_file("Error:Resolve 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            #p4Path = get_p4Path(paths)
            #p4.run("revert", "-k", paths)
            files = p4.run_resolve('-n',paths)
            json_str = json.dumps(files)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_FstatFiles(paths: list):
    if not paths:
        log_to_file("Error:Fstat 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            #p4Path = get_p4Path(paths)
            #p4.run("revert", "-k", paths)
            files =  p4.run_fstat(paths)
            json_str = json.dumps(files)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_LockFiles(paths: list): 
    if not paths:
        log_to_file("Error:Lock 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            #p4Path = get_p4Path(paths)
            #p4.run("revert", "-k", paths)
            addFiles =  p4.run_add(paths)
            editFiles =  p4.run_edit(paths)
            lockFiles = p4.run_lock(paths)
            json_str = json.dumps(lockFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_UnLockFiles(paths: list):
    if not paths:
        log_to_file("Error:Lock 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            unLockFiles = p4.run_unlock(paths)
            json_str = json.dumps(unLockFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_FstatDir(path: str):
    if not path:
        log_to_file("Error:commit 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            #p4.run("revert", "-k", paths)
            files =  p4.run_fstat('-T','otherLock4,otherLock3,otherLock2,otherLock1,otherLock,ourLock,clientFile',p4Path)
            json_str = json.dumps(files)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)


def p4_revert(path: str):
    if not path:
        log_to_file("Error:revert 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            p4.run("revert", "-k", p4Path)
            for msg in p4.messages:
                log_to_file(msg)
            cleanFiles = p4.run("clean", "-a", "-d", "-e", "-m", p4Path)
            for file in cleanFiles:
                log_to_file(file)

            json_str = json.dumps(p4.messages)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_revert_K_Files(paths: list):
    if not paths:
        log_to_file("Error:revert-K 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            revertFiles = p4.run_revert('-k',paths)
            json_str = json.dumps(revertFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_revertFiles(paths: list):
    if not paths:
        log_to_file("Error:revert 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            # p4.run_edit(paths)
            # revertFiles = p4.run_revert(paths)
            cleanFiles = p4.run("clean", "-a", "-d", "-e", "-m", paths)
            json_str = json.dumps(cleanFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")      
            weite_to_log(f"执行revert成功：{json_str}")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)


def p4_commit(path: str, commmitMsg: str, force: bool = False):
    if not path:
        log_to_file("Error:commit 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            for msg in p4.messages:
                log_to_file(msg)
            # generate submit path
            p4Path = get_p4Path(path)
            # clean workspace
            p4.run("revert", "-k", p4Path)
            for msg in p4.messages:
                log_to_file(msg)
            # reconcile offline work
            if force:
                p4.run_sync("-k", p4Path)

            changelist = p4.fetch_change()
            # clean files or else 'default' will add to this changelist
            changelist["files"] = ""
            changelist["Description"] = commmitMsg
            changelist = p4.save_change(changelist)
            changeId = -1
            for changeStr in changelist:
                if "Change" in changeStr and "created." in changeStr:
                    changeId = changeStr.split()[1]
                    
            # reconcile file to changelist
            reconcileFiles = p4.run_reconcile("-c", changeId,
                 '-e', '-a', '-d', "-m", p4Path)
            for msg in p4.messages:
                log_to_file(msg)
            if not check_reconcileFiles_legal(reconcileFiles):
                p4.run_change("-d", changeId)
                log_to_file("no file need to commit!")
                return False
            p4.run_submit('-c', changeId)
            for msg in p4.messages:
                log_to_file(msg)
            return True
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)


p4_pre_user_reconcile_rets = ("trigger wolrdx_pre_reconcile", "enter password")

def check_reconcileFiles_legal(reconcileFiles):
    if not reconcileFiles:
        return False
    else:
        # p4这个傻卵！加了pre-user-reconcile的trigger后run_reconcile的返回值里会带上trigger的日志
        # 需要检查一下是不是真的reconcile出来的文件了
        # 比如本身没有文件改动，会固定输出一个这样的列表['Trigger wolrdx_pre_reconcile .181s\n', 'Enter password: \nUser admin logged in.']
        count = 0
        for file in reconcileFiles:
            if isinstance(file, dict) or (not file.lower().startswith(p4_pre_user_reconcile_rets)):
                log_to_file(file)
                count = count + 1

        return count > 0

def p4_commitpathlist(paths: list, commmitMsg: str, force: bool = False):
    p4 = getP4Client()
    reconcileFilesList = []
    changeId = -1
    try:
        with p4.connect():
            for msg in p4.messages:
                log_to_file(msg)

            changelist = p4.fetch_change()
            changelist["files"] = ""
            changelist["Description"] = commmitMsg
            changelist = p4.save_change(changelist)
            changeId = -1
            for changeStr in changelist:
                if "Change" in changeStr and "created." in changeStr:
                    changeId = changeStr.split()[1]

            for path in paths:
                if not path:
                    continue
                # generate submit path
                p4Path = get_p4Path(path)
                p4.run("revert", "-k", p4Path)
                reconcileFiles = p4.run_reconcile(
                    "-c", changeId, '-e', '-a', '-d', "-m", p4Path)
                if check_reconcileFiles_legal(reconcileFiles):
                    reconcileFilesList += reconcileFiles
            # do submit
           
            if not reconcileFilesList:
                p4.run_change("-d", changeId)
                log_to_file("no file need to commit!")
                return False
            if changeId != -1:
                p4.run_submit('-c', changeId)

            weite_to_log(f"开始提交 {changeId} {str(reconcileFilesList)}")
            for msg in p4.messages:
                log_to_file(msg)
                weite_to_log(f"p4输出 {msg}")
            weite_to_log(f"提交结束 {changeId}")
            return True
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_add_to_changelist(paths: list, changeId: str, msg: str):
    p4 = getP4Client()
    reconcileFilesList = []
    try:
        with p4.connect():
            if changeId == "New":
                changelist = p4.fetch_change()
                changelist["files"] = ""
                changelist["Description"] = msg
                changelist = p4.save_change(changelist)
                changeId = -1
                for changeStr in changelist:
                    if "Change" in changeStr and "created." in changeStr:
                        changeId = changeStr.split()[1]
            
            for path in paths:
                if not path:
                    continue
                p4Path = get_p4Path(path)
                p4.run("revert", "-k", p4Path)
                if changeId == "default":
                    reconcileFiles = p4.run_reconcile('-e', '-a', '-d', "-m", p4Path)
                else:
                    reconcileFiles = p4.run_reconcile(
                        "-c", changeId, '-e', '-a', '-d', "-m", p4Path)
                    
                if check_reconcileFiles_legal(reconcileFiles):
                    reconcileFilesList += reconcileFiles

            if not reconcileFilesList:
                if changeId != "default":
                    p4.run_change("-d", changeId)
                log_to_file("returnStrStart ", "NoChangeId", " returnStrEnd")
            else:
                log_to_file("returnStrStart ", changeId, " returnStrEnd")
            
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        
def get_latest_all_info(path: str):
    if not path:
        log_to_file("Error:get_latest_all_info 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            changes = p4.run("changes", "-m", 1, p4Path)
            if len(changes) > 0:
                changeInfo = changes[0]
            changeInfo['desc'] = p4.run_describe(
                '-s', changeInfo['change'])[0]['desc']

            json_str = json.dumps(changeInfo)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
        return changeInfo
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def handle_reconcileFiles(reconcileFiles):
    newReconcileFiles = []
    for file in reconcileFiles:
        if isinstance(file, dict) or (not file.lower().startswith(p4_pre_user_reconcile_rets)):
            newReconcileFiles.append(file)
    return newReconcileFiles

def get_all_change_file(path: str):
    if not path:
        log_to_file("Error:get_all_change_file 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            reverted_files = p4.run_revert('-k', p4Path)
            reconcileFiles = p4.run_reconcile('-n', p4Path)
            reconcileFiles = handle_reconcileFiles(reconcileFiles)
            json_str = json.dumps(reconcileFiles)
            if len(json_str) == 0:
                reconcileFiles = p4.run_reconcile('-n', '-a', p4Path)
                reconcileFiles = handle_reconcileFiles(reconcileFiles)
                json_str = json.dumps(reconcileFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
            weite_to_log(f"获取目录：{path} 的改动文件  {json_str}")

    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def get_all_change_file_byPathList(paths: list, commmitMsg: str, force: bool = False):
    if not paths:
        log_to_file("get_all_change_file_byPathList 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            needReLockPaths = []
            haslockFiles = p4.run_fstat('-T','ourLock,clientFile',paths)
            for i in range(len(haslockFiles)):
                if haslockFiles[i].get('ourLock') != None :
                    needReLockPaths.append(haslockFiles[i].get('clientFile'))

            p4.run_revert('-k', paths)
            reconcileFiles = p4.run_reconcile('-n','-ead', paths)
            json_str = json.dumps(reconcileFiles)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
            if len(needReLockPaths) >0:
                p4.run_edit(needReLockPaths)
                p4.run_lock(needReLockPaths)

    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)


def get_changes_info(path: str, maxCount=5):
    if not path:
        log_to_file("get_changes_info 路径为空")
    p4 = getP4Client()
    try:
        changeInfos = []
        with p4.connect():
            p4Path = get_p4Path(path)
            changes = p4.run("changes", "-m", maxCount, p4Path)
            for i in range(0, len(changes)):
                changeInfo = changes[i]
                changeInfo["time"] = int(changeInfo["time"])
                changeInfo["changeId"] = int(changeInfo["change"])
                changeInfo['desc'] = p4.run_describe('-s', changeInfo['change'])[0]['desc']
                changeInfos.append(changeInfo)
        json_str = json.dumps(changeInfos)
        log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_checkout_or_add(path: str):
    if not path:
        log_to_file("Error: 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            p4.run("edit", p4Path)
            if "..." in p4Path:
                metaPath = p4Path[:-4] + '.meta'
            else:
                metaPath = p4Path + '.meta'
            p4.run("edit", metaPath)
            msg = str(p4.messages)
            msgs = p4.messages.copy()
            if msg and "file(s) not on client" in msg:
                p4.run("add", p4Path)
                msgs.extend(p4.messages)
                p4.run("add", metaPath)
                msgs.extend(p4.messages)
            for line in msgs:
                log_to_file(line)
            json_str = str(msgs)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_delete(path: str):
    if not path:
        log_to_file("Error: 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            p4Path = get_p4Path(path)
            p4.run("delete", p4Path)
            msgs = p4.messages.copy()
            if "..." in p4Path:
                metaPath = p4Path[:-4] + '.meta'
            else:
                metaPath = p4Path + '.meta'
            p4.run("delete", metaPath)
            msgs.extend(p4.messages)
            json_str = str(msgs)
            log_to_file("returnStrStart ", json_str, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_print_file(path:str):
    if not path:
        log_to_file("Error: 路径为空")
    p4 = getP4Client()
    try:
        with p4.connect():
            file_content = p4.run("print", path)
            log_to_file("returnStrStart ", file_content, " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)

def p4_get_local_changelist(printresult: bool):
    p4 = getP4Client()
    try:
        with p4.connect():
            changeList = p4.run_changes("-s", "pending", "-u" , args.p4user, "-c", args.p4workspace)
            json_str = json.dumps(changeList)
            if printresult:
                log_to_file("returnStrStart ", json_str, " returnStrEnd")
            return changeList
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        
def weite_to_log(log):
    file_path = args.logFile
    content_to_add = log
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    line_to_add = f'{formatted_time}  {content_to_add}\n'
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(line_to_add)


def check_client_into():
    p4 = P4()
    p4.user = "admin"
    p4.password = "Admin@P4!@#"
    p4.charset = "utf8"
    p4.track = 1
    p4.exception_level = 1
    p4.port = "p4-world.funplus.com.cn:1666"
    try:
        with p4.connect():
            p4.run_login()
            workspaces = p4.run_client("-o", args.p4workspace)
            workspaces[0]["Root"].replace("\\","/").replace("//","/")
            if not are_directories_same(workspaces[0]["Root"], args.p4Root):
                log_to_file("Error:", f"当前目录 {args.p4Root} 和配置的workspace {args.p4workspace} 不匹配！这可能会导致P4相关操作异常，请到【Unity - Window - P4】中配置正确的workspace信息")
                return False
            return True
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        return False

def are_directories_same(dir1, dir2):
    canonical_dir1 = os.path.realpath(dir1)
    canonical_dir2 = os.path.realpath(dir2)
    return canonical_dir1.lower() == canonical_dir2.lower()
# 获取文件当前版本ID()
def p4_file_current_version(paths: list,printresult: bool):
    if not paths or len(paths) <= 0:
        log_to_file("Error: 路径为空")
        return
    p4 = getP4Client()
    try:
        with p4.connect():
            headrevdic = {}
            fstat_info = p4.run_fstat(paths)
            if not fstat_info or len(fstat_info) == 0:
                log_to_file("Error: 未获取到版本数据")
                return
            for info in fstat_info:
                if 'clientFile' and 'haveRev' in info:
                    client_file = info['clientFile']
                    haverev = info['haveRev']
                    headrevdic[client_file] = haverev
            if printresult:
                log_to_file("returnStrStart ", json.dumps(headrevdic), " returnStrEnd")
            return headrevdic
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        weite_to_log(f"file_current_version失败：{warnings}, {errors}")
        
#还原到上一个版本
def p4_undo_reversion(paths: list):
    if not paths or len(paths) == 0:
        log_to_file("Error: 路径为空")
        return
    haverev_dics = p4_file_current_version(paths, False)
    if not haverev_dics or len(haverev_dics) == 0 or len(haverev_dics) != len(paths):
        log_to_file("Error: 版本数据错误")
        return
    p4 = getP4Client()
    try:
        with p4.connect():
            padding_changelist = p4_get_local_changelist(False)
            changelistid = 0
            for changelist in padding_changelist:
                if changelist['desc'] == 'undo reversion changelist\n':
                    changelistid = int(changelist['change'])
                    break
            if changelistid == 0:
                changelist_info = p4.save_change({'Change': 'new', 'Description': 'undo reversion changelist'})[0]
                changelistid = int(changelist_info.split()[1])
            message = []
            for key, value in haverev_dics.items():
                if key == "":
                    continue
                target_rev = int(value) - 1
                if target_rev == 0:
                    continue
                command = "%s#%d" % (key, target_rev)
                p4.run("undo", "-c", changelistid, command)
                for msg in p4.messages:
                    message.append(msg)
            log_to_file("returnStrStart ", json.dumps(message), " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        weite_to_log(f"执行reversion失败：{warnings}, {errors}")
#还原文件到最新
#先revert然后getlast
def p4_revert_and_getlastversion(paths: list):
    if not paths or len(paths) == 0:
        log_to_file("Error: 文件列表为空")
        return
    p4 = getP4Client()
    try:
        with p4.connect():
            message = []
            for path in paths:
                if path == "":
                    continue
                path_list = p4.run("where", path)
                message = p4.messages
                if not path_list or len(path_list) == 0:
                    continue
                if 'depotFile' in path_list[0]:
                    p4.run_revert(path_list[0]['depotFile'])
                    command = f"{path}#head"
                    p4.run_sync(command)
                    for msg in p4.messages:
                        message.append(msg)
            log_to_file("returnStrStart ", json.dumps(message), " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)
        weite_to_log(f"执行revert_and_getlastversion失败：{warnings}, {errors}")


def p4_check_guid_modified(paths: list):
    if not paths or len(paths) == 0:
        log_to_file("Error: 文件列表为空")
        return
    p4 = getP4Client()
    try:
        with p4.connect():
            errors = ""
            for path in paths:
                if path == "":
                    continue
                p4Path = get_p4Path(path)
                rets = p4.run("diff", "-f", p4Path)
                guid1 = None
                guid2 = None
                for line in rets:
                    if isinstance(line, str):
                        if(line.startswith("< guid:")):
                            guid1 = line.split(":")[1].strip()
                        elif(line.startswith("> guid:")):
                            guid2 = line.split(":")[1].strip()
                            if(guid1 != guid2):
                                msg = "meta GUID has been modified " + p4Path + "," + guid1 + "," + guid2
                                errors = f"{errors}{msg}\n"
                            break
            if errors != "":
                log_to_file("Error:", errors)
            else:
                log_to_file("returnStrStart ", "success", " returnStrEnd")
    except P4Exception as e:
        warnings = '\n'.join(e.warnings)
        errors = '\n'.join(e.errors)
        log_to_file("Error:", warnings, errors)


# mac上重定向输出有问题，把日志输出到文件里
def log_to_file(*_args):
    if not args.retLogFile:
        return
    message = "".join(map(str, _args))
    #print(message)
    with open(args.retLogFile, 'a', encoding='utf-8') as log_file:
        log_file.write(message + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4 工具脚本')
    parser.add_argument('--p4user', type=str, help='当前的p4用户账号')
    parser.add_argument('--p4workspace', type=str, help='当前工作区')
    parser.add_argument('--dir', type=str, help='操作目标目录')
    parser.add_argument('--filePath', type=str, help='操作目标文件。文件内容是文件列表，用,分隔开')
    parser.add_argument('--cmd', type=str,
                        help='操作行为。可传参数：update;commit;revert;get_latest_all_info')
    parser.add_argument('--msg', type=str, help='操作日志')
    parser.add_argument('--changeId', type=str, help='ChangeId')
    parser.add_argument('--logFile', type=str, help='LogFile')
    parser.add_argument('--p4Root', type=str, help='当前P4路径')
    parser.add_argument('--max', type=str, help='获取提交记录的最大数量')
    parser.add_argument('--email', type=str, help='给飞书用户发消息的邮箱')
    parser.add_argument('--larkChatId', type=str, help='给飞书群发消息的群ID')
    parser.add_argument('--retLogFile', type=str, help='Path to the log file')
    args = parser.parse_args()

    if False:
        pass
    else:
        if args.cmd == 'get_all_change_file':
            get_all_change_file(args.dir)

        if args.cmd == 'commitDir':
            p4_commit(args.dir, args.msg)

        if args.cmd == 'commitFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                # log_to_file(files)
                p4_commitpathlist(files, args.msg)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)

        if args.cmd == 'revert':
            p4_revert(args.dir)

        if args.cmd == 'get_latest_all_info':
            get_latest_all_info(args.dir)

        if args.cmd == 'update':
            p4_update(args.dir)
        
        if args.cmd == 'update_f':
            p4_update_f(args.filePath)

        if args.cmd == 'updateFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_UpdateFiles(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)

        if args.cmd == 'checkMetasGuidModified':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_check_guid_modified(files)

            if os.path.isfile(args.filePath):
                os.remove(args.filePath)

        if args.cmd == 'fstatFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_FstatFiles(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)
            
        if args.cmd == 'fstatDir':
            p4_FstatDir(args.dir)  

        if args.cmd == 'get_resolvefiles_info':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                Get_ResolveFiles_Info(files)

            if os.path.isfile(args.filePath):
                os.remove(args.filePath)  

        if args.cmd == 'lockFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_LockFiles(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)

        if args.cmd == 'unLockFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_UnLockFiles(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)  

        if args.cmd == 'revert_K_Files':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_revert_K_Files(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath) 

        if args.cmd == 'revertFiles':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_revertFiles(files)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath) 
        
        if args.cmd == 'get_all_change_file_by_pathList':
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                get_all_change_file_byPathList(files, args.msg)
            
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)
        
        if args.cmd == 'checkout_or_add':
            p4_checkout_or_add(args.filePath)
        
        if args.cmd == 'mark_for_delete':
            p4_delete(args.filePath)

        if args.cmd == 'p4_print_file':
            p4_print_file(args.filePath)
            
        if args.cmd == "p4_get_local_changelist":
            p4_get_local_changelist(True)
            
        if args.cmd == "p4_add_to_changelist":
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_add_to_changelist(files, args.changeId, args.msg)
            if os.path.isfile(args.filePath):
                os.remove(args.filePath)
                
        if args.cmd == 'updateF':
            p4_updateF(args.dir)
        
        if args.cmd == "check_client_into":
            check_client_into()
        if args.cmd == "file_current_version":
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_file_current_version(files, True)
        if args.cmd == "undo_reversion":
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_undo_reversion(files)
        if args.cmd == "revert_getlastversion":
            with open(args.filePath, 'r', encoding='gbk') as file:
                content = file.read()
                files = content.split(",")
                p4_revert_and_getlastversion(files)
                
        if args.cmd == "get_changes_info":
            get_changes_info(args.dir, int(args.max))

        if args.cmd == "send_ddMsg_user":
            # LarkTools.send_ddMsg_user(args.email, args.msg)
            pass

        if args.cmd == "send_ddMsg":
            # LarkTools.send_ddMsg(args.larkChatId, args.msg)
            pass

