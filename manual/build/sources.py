# -*- coding: utf-8 -*-
"""「④ 异常特征」表格「来源」列的取值表。

S = 脚本：该判据在 er_check.py 有等价实现，附函数名与关键行（行号为承载该判据的
          c.add / c.hit / persist_add 调用所在行，便于直接定位复核）。
E = 经验：脚本没有该判据，属现场经验补充。

每条与 data_win / data_linux 里 abns 的行一一对应、顺序一致；数量不符会在构建时报错。
"""

S = lambda f, ln: "S|%s|%s" % (f, ln)
E = "E"


def rep(f, ln, n):
    return [S(f, ln)] * n


SRC = {
    # ---------------- 第 1 章 Windows ----------------
    # 1.1 补丁与版本：脚本只输出基础信息与高风险监听端口，以下为现场经验判据
    "1.1": [E, E, E, E, E],
    "1.2": [S("win_accounts", 1392), S("win_accounts", 1398), S("win_accounts", 1437),
            S("win_accounts", 1437), E, E],
    # 1.3：IFEO 为脚本判据（win_autoruns 内联实现），见末行
    "1.3": [S("win_autoruns", 1546), S("win_autoruns", 1546), E, E, E, E,
            S("win_autoruns", "1489–1500")],
    "1.4": [S("win_tasks", 1586), S("win_tasks", 1586), E, E, E, E],
    "1.5": [S("_priv_service_rows", 2476), S("win_services", 1630), E,
            S("win_drivers_certs_firewall", 9118), S("win_services", 1634), E],
    "1.6": [S("win_process_net", 1841), S("win_process_net", 1841), S("win_process_net", 1812),
            S("win_process_net", 1853), E, S("win_process_net", 1790)],
    "1.7": [E, S("win_files", 2101), S("win_files", 2042), S("win_files", 2154), E, E],
    "1.8": [S("win_security_advanced", 8542), S("win_logs", 2215), S("win_logs", 2248),
            S("win_logs", 2230), S("win_logs", 2279), E],
    "1.9": [S("win_logs_advanced", 5672), S("win_logs_advanced", 6199), E,
            S("win_logs_advanced", 6330), E, E],
    "1.10": [E, S("win_security_advanced", 8646), S("win_security_advanced", 8683),
             S("win_security_advanced", 8728), E, S("win_security_advanced", 8636)],
    "1.11": [S("win_wmi_subscription", 3176), S("win_wmi_subscription", 3179),
             S("win_wmi_subscription", 3182), S("win_wmi_subscription", 3186), E,
             S("win_wmi_subscription", 3191)],
    "1.12": [S("win_hijack_points", 3220), S("win_hijack_points", 3289),
             S("win_hijack_points", 3289), S("win_hijack_points", 3289), E],
    "1.13": [S("win_bits", 4809), S("win_bits", 4809), E, S("win_bits", 4815)],
    "1.14": [S("win_av_status", 4851), S("win_av_status", 4866), E,
             S("win_av_status", 4847), S("win_av_status", 4866), E],
    # 1.15：RunMRU 与 Credentials 目录脚本均未采集
    "1.15": [S("win_credentials_config", 4894), S("win_credentials_config", 4900), E, E, E],
    "1.16": [S("win_network_config", 4922), S("win_network_config", 4945),
             S("win_network_config", 4937), E, S("win_network_config", 4971), E],
    "1.17": [S("win_shares", 5502), S("win_shares", 5502), S("win_shares", 5510),
             S("win_shares", 5519), E],
    "1.18": rep("win_process_anomaly", 9086, 4) + [E, E],
    "1.19": [S("win_malware_dossier", 10641), S("win_malware_dossier", 10641), E, E, E, E],
    "1.20": [S("win_drivers_certs_firewall", 9128), S("win_drivers_certs_firewall", 9118),
             S("win_drivers_certs_firewall", 9135), S("win_drivers_certs_firewall", 9144), E, E],
    "1.21": [S("_priv_service_rows", 2476), S("_priv_always_install_elevated", 2560), E,
             S("_priv_hidden_tasks", 2993), E],
    # 1.22：IFEO 由 _hj_adv_accessibility 实现，且按子键路径与 1.3 去重
    "1.22": [S("_hj_adv_accessibility", 3572), S("win_autoruns", 1471), E,
             S("_hj_adv_accessibility", 3623), E, S("win_hijack_advanced", 4238)],
    "1.23": [S("win_net_config", 4777), S("win_files", 2119), S("win_net_config", 4536), E,
             S("win_net_config", 4652), S("win_net_config", 4541)],
    "1.24": [S("win_proc_deep", 4980), E, E, S("_proc_javaagent", 4988), E, E],
    "1.25": [E, S("r10_baseline_step", 27505), S("r10_baseline_step", 27505)],
    "1.26": rep("r11_custom_checks", 18620, 4) + [E],
    "1.27": [S("r13_rules_checks", 21328), S("r13_rules_checks", 21328), E],
    "1.28": [S("win_active_setup", 4290), S("win_active_setup", 4290), E,
             S("win_active_setup", 4296), S("win_active_setup", 4300)],
    "1.29": [S("win_ps_profiles", 4373), S("win_ps_profiles", 4373), E,
             S("win_ps_profiles", 4373), S("win_ps_profiles", 4380)],
    "1.30": [S("win_office_addins", 4411), S("win_office_addins", 4424), E,
             S("win_office_addins", 4414), E],
    "1.31": rep("win_persist_attribution", 8384, 2) + [E] + rep("win_persist_attribution", 8384, 2),
    "1.32": rep("win_weblog_step", 17182, 5),
    "1.33": rep("win_webshell_step", 17187, 5),

    # ---------------- 第 2 章 Linux ----------------
    # 2.1 内核与版本：脚本只输出基础信息，CVE 与 EOL 判定均为经验
    "2.1": [E, E, E, E, E],
    "2.2": [S("linux_accounts", 10867), S("linux_accounts", 10867), S("linux_accounts", 10869),
            S("linux_accounts", 10944), S("linux_accounts", 10954), E],
    "2.3": [S("linux_history", 11004), S("linux_history", 10986), S("linux_history", 10986),
            S("linux_history", 10986), E, E],
    "2.4": [S("linux_cron", 11398), S("linux_cron", 11398), S("linux_cron", 11398), E,
            S("linux_cron", 11416), E],
    "2.5": [S("linux_autoruns", 11313), S("linux_autoruns", 11313), E,
            S("linux_autoruns", 11359), S("linux_autoruns", 11336), S("linux_autoruns", 11313)],
    "2.6": [S("linux_backdoors", 11483), S("linux_backdoors", 11563),
            S("linux_backdoors", 11432), E, E, E],
    "2.7": [S("linux_net_proc", 11236), S("linux_net_proc", 11236),
            S("linux_net_proc", 11264), E, S("linux_net_proc", 11264), E],
    "2.8": [S("linux_files", 11681), S("linux_files", 11681), S("linux_files", 11687), E, E,
            S("linux_files", 11691)],
    "2.9": [S("linux_logs", 11868), S("linux_logs", 11892), S("linux_logs", 11897), E, E, E],
    "2.10": [S("linux_hidden_procs", 12627), S("linux_hidden_procs", 12627),
             S("linux_hidden_procs", 12668), E, E, E],
    "2.11": [S("linux_kernel_modules", 12698), S("linux_kernel_modules", 12695), E, E,
             S("linux_kernel_modules", 12690), E],
    "2.12": rep("linux_capabilities", 12712, 4) + [E, S("linux_capabilities", 12718)],
    "2.13": rep("linux_ssh_surface", 12773, 4) + [E, E],
    # 2.14：preload 本体由 2.6 覆盖，本行只作指向
    "2.14": [S("linux_backdoors", 11483), S("linux_injection_points", 12826),
             S("linux_injection_points", 12826), S("linux_injection_points", 12826),
             S("linux_injection_points", 12830), E],
    "2.15": rep("linux_sched_jobs", 12915, 4) + [S("linux_sched_jobs", 12919)],
    "2.16": rep("linux_web_layer", 12890, 3) + [E, S("linux_web_layer", 12890)],
    "2.17": rep("linux_malware_families", 12980, 3) + [E, E, S("linux_malware_families", 12980)],
    "2.18": [S("linux_lateral_and_tools", 13019), S("linux_ssh_surface", 12770), E,
             S("linux_lateral_and_tools", 13019), S("linux_lateral_and_tools", 13019),
             S("linux_lateral_and_tools", 13022)],
    "2.19": rep("linux_log_integrity", 13091, 4) + [E, E],
    "2.20": [S("linux_audit_logs", 12375), S("linux_audit_logs", 12367), E,
             S("linux_audit_logs", 12319), E, E],
    "2.21": [S("linux_pkg_verify", 13125), S("linux_pkg_verify", 13125), E,
             S("linux_pkg_verify", 13125), S("linux_pkg_verify", 13109)],
    "2.22": [E, E, E, E, S("linux_container_env", 13145)],
    "2.23": rep("linux_app_logs", 15302, 3) + [E, S("linux_app_logs", 15307)],
    "2.24": [E, S("linux_net_config", 14567), E, E, S("linux_net_config", 14567), E],
    "2.25": [S("linux_persistence", 13404), E, S("linux_cron", 11398), E, E,
             S("linux_persistence", 13404)],
    "2.26": [S("linux_proc_deep", 15450), S("linux_proc_deep", 15450),
             S("linux_proc_deep", 15493), E, S("_proc_javaagent", 4988), E],
    "2.27": [E, S("r10_baseline_step", 27505), S("r10_baseline_step", 27505)],
    "2.28": rep("r11_custom_checks", 18620, 4) + [E],
    "2.29": [S("r13_rules_checks", 21328), S("r13_rules_checks", 21328), E, E],
    "2.30": rep("r12_container_k8s", 14260, 5) + [E],
    "2.31": rep("linux_weblog_step", 17192, 5),
    "2.32": rep("linux_webshell_step", 17197, 5),
}


def apply(items):
    """把来源写回 abns（不改动原描述文本）。数量不符直接报错，避免错位。"""
    bad = []
    for it in items:
        want = SRC.get(it["no"])
        if want is None:
            bad.append((it["no"], len(it["abns"]), 0))
            continue
        if len(want) != len(it["abns"]):
            bad.append((it["no"], len(it["abns"]), len(want)))
            continue
        new = []
        for ab, src in zip(it["abns"], want):
            new.append(ab if ab.count("|") >= 2 else ab + "|" + src)
        it["abns"] = new
    if bad:
        raise SystemExit("来源列数量不匹配（章节, 现有行数, 标注数）: %s" % bad)
