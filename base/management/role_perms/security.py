perms = {
    'auth': [
        'list_permission',

        # role
        'list_role',
        'list_role_perms',
        'list_role_users',
    ],
    'base': [
        # user
        'list_user',
        'list_user_active',
        'detail_user',
        'active_user',
        'update_user_perms',
        'update_user_roles',
        # user security
        'list_address_control',
        'change_address_control',
        'delete_address_control',
        'view_login_period',
        'change_login_period',
        'list_login_terminal',
        'change_login_terminal',
        'lock_user',

        # operation log
        'view_operation_log',
        'delete_operation_log',
        'download_operation_log',
        'analysis_log',

        # system settings
        'view_system_settings',
        'change_system_settings',

        # resource
        'list_resource',
        'create_resource',
        'update_resource',
        'detail_resource',
        'delete_resource',
    ],
    'vserver': [
        # dashboard
        'get_dashboard',
        'sec_dashboard',

        # data_center
        'list_datacenter',
        'detail_dc',

        # cluster
        'list_cluster',
        'detail_cluster',
        'schedule_policy_list',
        'schedule_policy_detail',
        'migration_policy_list',

        # commission 待办
        'update_commission',
        'list_commission',
        'create_commission',

        # host
        'list_host',
        'detail_host',

        # disk
        'list_disk',
        'detail_disk',

        # vm
        'list_vm',
        'detail_vm',
        'update_vm_security',
        'vm_create_disk',
        'create_vnic',
        'list_vnics',
        'delete_vinc',
        'list_export_domain_vm',
        'list_vcenter_vm',
        'list_kvm_vms',
        'list_export_domain_vms',
        'vm_event_list',
        'vm_host_device_list',

        # storage_domain
        'update_sd',
        'list_storage',
        'detail_storage',
        'list_storage_templates',

        # data_archive
        'list_data_archive',

        # alarm_rule
        'list_alarm_rule',
        'detail_event_report',

        # alarm_report
        'list_event_report',
        'delete_event_report',
        'read_event_report',

        # role
        'list_alarm_role',

        # inspection
        'list_inspection',
        'detail_inspection',

        # performance
        'list_performance',
        'detail_performance',

        # asset
        'list_asset',

        # firewall
        'list_firewall_policy',
        'detail_firewall_policy',
        'create_firewall_policy',
        'update_firewall_policy',
        'delete_firewall_policy',

        'list_firewall_rule',
        'create_firewall_rule',
        'delete_firewall_rule',

        'list_firewall_group',
        'detail_firewall_group',
        'create_firewall_group',
        'update_firewall_group',
        'delete_firewall_group',

        # floating_ip
        'list_floating_ip',
        'create_floating_ip',
        'delete_floating_ip',

        # router
        'list_router',
        'create_router',
        'update_router',
        'delete_router',
        'detail_router',
        'set_router_gateway',
        'add_router_interface',
        'remove_router_interface',

        # network
        'get_network_topology',
        'list_network',
        'detail_network',

        # subnet
        'list_subnet',
        'detail_subnet',
        'release_port',
        'list_subnet_used_ip',

        # template
        'list_template',
        'detail_template',

        # ova
        'list_ova',
        'detail_ova',

        # image
        'list_image',
        'detail_image',

        # syslog
        # 'list_syslog',

        # snapshot
        'list_snapshot',

        # affinity_groups
        'list_affinity_group',
        'detail_affinity_group',

        # tags
        'list_tags',

        # monitor history
        'list_monitor_history',
        'detail_monitor_history',

        # qos
        'list_qos',
    ]
}
