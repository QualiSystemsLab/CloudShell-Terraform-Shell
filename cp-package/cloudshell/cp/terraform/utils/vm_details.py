from cloudshell.cp.terraform.actions.vm_details import VMDetailsActions


def create_vm_details(resource_config, app_name, tf_outputs, path, logger):
    """Create VM details data.

    :param resource_config: Terraform resource config
    :param app_name: App name
    :param path: Path
    :param logger: Logger
    :return: VM details data
    """
    return VMDetailsActions(
        resource_config,
        app_name,
        tf_outputs,
        path,
        logger,
    ).create()
