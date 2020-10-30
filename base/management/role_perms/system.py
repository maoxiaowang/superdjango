perms = {
    'auth': [
        # permission
        'list_permission',

        # role
        'list_role',
        'create_role',
        'update_role',
        'delete_role',
        'add_role_users',
        'remove_role_users',
        'list_role_perms',
        'list_role_users',
    ],
    'base': [
        # user
        'list_user',
        'create_user',
        'update_user',
        'detail_user',
        'delete_user',
        'reset_password',
        'update_user_roles',
        'list_address_control',
        'change_address_control',
        'delete_address_control',
        'list_user_active',

        # operation log
        'view_operation_log',
        # 'delete_operation_log',
        # 'download_operation_log',
        # 'analysis_log',

        # system settings
        'view_system_settings',
        'change_system_settings',
    ],
    'vserver': [
        # dashboard
        'get_dashboard',
        'sec_dashboard',
        
        # data_center
        'list_datacenter',
        'detail_dc',
        'create_dc',
        'update_dc',
        'delete_dc',
        'update_dc_security',
        'set_sys_init',
        'list_sys_init',

        #
        # 'update_security',  # todo 安全管理员权限

        # cluster
        'list_cluster',
        'detail_cluster',
        'create_cluster',
        'update_cluster',
        'reset_emulated_machine',
        'delete_cluster',
        'schedule_policy_list',
        'schedule_policy_detail',
        'migration_policy_list',

        # host
        'list_host',
        'detail_host',
        'create_host',
        'update_host',
        'delete_host',
        'activate_host',
        'deactivate_host',
        'refresh_host',
        'host_kernel_reset',
        'list_host_power',
        'create_host_power',
        'update_host_power',
        'delete_host_power',
        'host_power_action',
        'host_register_certificate',
        'set_host_managing_storage_pools',
        'host_re_install',
        'host_nic_bond',
        'host_enable_ha',
        'set_host_qos',
        'host_attachments_network',

        # disk
        'list_disk',
        'detail_disk',
        'create_disk',
        'update_disk',
        'delete_disk',
        'copy_disk',
        'move_disk',
        'export_disk',
        'upload_disk_file',
        'download_disk',
        'is_active_disk',

        # vm
        'list_vm',
        'detail_vm',
        'create_vm',
        'update_vm',
        'delete_vm',
        'power_on_vm',
        'power_down_vm',
        'list_export_domain_vm',
        'detail_export_domain_vm',
        'create_export_domain_vm',
        'update_export_domain_vm',
        'delete_export_domain_vm',
        'list_vnics',
        'update_vinc',
        'delete_vm_host_device',
        'template_create_vm',
        'list_vcenter_vm',
        'vcenter_import_vm',
        'import_vm_from_kvm',
        'list_kvm_vms',
        'suspend_vm',
        'shutdown_vm',
        'stop_vm',
        'reboot_vm',
        'vm_consoles',
        'change_cd',
        'migrate_vm',
        'cancel_migrate_vm',
        'clone_vm',
        'add_template',
        'export_domain',
        'export_vm_as_ova',
        'list_export_domain_vms',
        'detail_ova_info',
        'update_vm_tags',
        'vm_create_disk',
        'attach_disk',
        'detach_disk',
        'vm_host_device_add_list',
        'vm_host_device_list',
        'vm_event_list',

        # alarm_report
        'list_event_report',
        'detail_event_report',
        'delete_event_report',
        'read_event_report',
        'export_event_report',

        # rule
        'list_alarm_rule',
        'detail_alarm_rule',
        'delete_alarm_rule',
        'update_alarm_rule',
        'create_alarm_rule',

        # role
        'list_alarm_role',
        'create_alarm_role',
        'delete_alarm_role',

        # inspection
        'list_inspection',
        'detail_inspection',
        'create_inspection',
        'update_inspection',
        'delete_inspection',
        'export_inspection',
        'oneclick_inspection',

        # performance
        'list_performance',
        'detail_performance',
        'export_performance',

        # asset
        'list_asset',
        'download_asset',

        # storage
        'list_storage',
        'detail_storage',
        'create_sd',
        'update_sd',
        'delete_sd',
        'attach_sd',
        'detach_sd',
        'active_sd',
        'maintain',
        'iscsi_descovery',
        'iscsi_login',
        'update_ovf',
        'list_iso_images',
        'list_storage_templates',

        # subnet
        'list_subnet',
        'create_subnet',
        'update_subnet',
        'detail_subnet',
        'delete_subnet',
        'list_subnet_used_ip',
        'release_port',

        # template
        'list_template',
        'detail_template',
        'create_template',
        'update_template',
        'delete_template',
        'list_domain_template',
        'export_template',
        'compute_export_to_domain',
        'list_host_path_ova',
        'delete_domain_template',
        'import_template_from_ova',
        'get_export_template_info',
        'detail_template_ova_info',

        # ova
        'list_ova',
        'detail_ova',
        'create_ova',
        'update_ova',
        'delete_ova',

        # image
        'list_image',
        'create_image',
        'detail_image',
        'delete_image',
        'download_image',
        'upload_image_file',
        'check_image_upload',

        # syslog
        'list_syslog',
        'delete_syslog',

        # data_archive
        'list_data_archive',
        'create_data_archive',
        'update_data_archive',
        'delete_data_archive',

        # firewall
        'list_firewall_group',
        'delete_firewall_group',
        'list_firewall_rule',

        # floating_ip
        'list_floating_ip',

        # router
        'list_router',

        # network
        'list_network',
        'detail_network',
        'create_network',
        'update_network',
        'delete_network',
        'get_network_topology',

        # snapshot
        'create_snapshot',
        'list_snapshot',
        'list_snapshot_disks',
        'commit_snapshot',
        'preview_snapshot',
        'undo_snapshot',
        'delete_snapshot',

        # affinity_groups
        'list_affinity_group',
        'create_affinity_group',
        'detail_affinity_group',
        'update_affinity_group',
        'delete_affinity_group',

        # tags
        'list_tags',
        'create_tags',
        'update_tags',
        'delete_tags',

        # monitor history
        'list_monitor_history',
        'detail_monitor_history',

        # qos
        'list_qos',
        'create_qos',
        'update_qos',
        'delete_qos',
    ]
}
