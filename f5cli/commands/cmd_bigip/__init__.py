"""Below are examples of using the CLI to interact with a BIG-IP.


    1. Install or upgrade an Automation Toolchain package
    ------------------------------------------
    The following are the examples of how to install, uninstall, upgrade, and verify the Declarative
    Onboarding package onto a BIG-IP.  ::
        $ f5 bigip extension package install --component do
        {
            "message": "Extension component package 'do' successfully installed version '1.10.0'"
        }

        $ f5 bigip extension package verify --component do
        {
            "installed": true,
            "installed_version": "1.10.0",
            "latest_version": "1.10.0"
        }

        $ f5 bigip extension package uninstall --component do
        {
           "message": "Successfully uninstalled extension component package 'do' version '1.10.0'"
        }

        $ f5 bigip extension package upgrade --component do --version 1.9.0
        {
            "message": "Successfully upgraded extension component package 'do' to version '1.9.0'"
        }


    2. Install an Automation Toolchain service
    ------------------------------------------
    The following is an example of how to configure a new service using AS3 ::

        $ f5 bigip extension service --component as3 --declaration as3_decl.json create
        {
            "declaration": {
                ...
            }
        }


"""

# pylint: disable=too-many-arguments

import click_repl
import click

from f5sdk.bigip import ManagementClient
from f5sdk.bigip.extension import ExtensionClient

from f5cli import docs, constants
from f5cli.utils import core as utils_core
from f5cli.commands.cmd_bigip import extension_operations
from f5cli.config import ConfigClient
from f5cli.cli import PASS_CONTEXT, AliasedGroup

HELP = docs.get_docs()


# group: bigip
@click.group('bigip',
             help=HELP['BIGIP_HELP'],
             cls=AliasedGroup)
def cli():
    """ group """


# group: extension - package, service
EXTENSION_COMPONENTS = ['do', 'as3', 'ts', 'cf']

@cli.group('extension',
           help=HELP['BIGIP_EXTENSION_HELP'])
def extension():
    """ group """


@extension.command('package',
                   help=HELP['BIGIP_EXTENSION_PACKAGE_HELP'])
@click.argument('action',
                required=True,
                type=click.Choice(['install', 'uninstall', 'upgrade', 'verify']))
@click.option('--component',
              required=True,
              type=click.Choice(EXTENSION_COMPONENTS))
@click.option('--version',
              required=False)
@click.option('--use-latest-metadata', is_flag=True)
@PASS_CONTEXT
def package(ctx, action, component, version, use_latest_metadata):
    """ command """
    auth = ConfigClient().read_auth(constants.AUTHENTICATION_PROVIDERS['BIGIP'])
    management_kwargs = dict(port=auth['port'], user=auth['user'], password=auth['password'])
    client = ManagementClient(auth['host'], **management_kwargs)

    kwargs = {}
    if version:
        kwargs['version'] = version
    if use_latest_metadata:
        kwargs['use_latest_metadata'] = use_latest_metadata

    if action == 'verify':
        ctx.log(extension_operations.verify_package(client, component, **kwargs))
    elif action == 'install':
        ctx.log(extension_operations.install_package(client, component, **kwargs))
    elif action == 'uninstall':
        ctx.log(extension_operations.uninstall_package(client, component, **kwargs))
    elif action == 'upgrade':
        ctx.log(extension_operations.upgrade_package(client, component, version))
    else:
        raise click.ClickException('Action {} not implemented'.format(action))


@extension.command('service',
                   help=HELP['BIGIP_EXTENSION_SERVICE_HELP'])
@click.argument('action',
                required=True,
                type=click.Choice(['create', 'delete', 'show', 'show-info',
                                   'show-failover', 'show-inspect', 'reset', 'trigger-failover']))
@click.option('--component',
              required=True,
              type=click.Choice(EXTENSION_COMPONENTS))
@click.option('--version',
              required=False)
@click.option('--declaration',
              required=False)
@click.option('--install-component',
              required=False,
              is_flag=True)
@PASS_CONTEXT
def service(ctx, action, component, version, declaration, install_component):
    """ command """
    auth = ConfigClient().read_auth(constants.AUTHENTICATION_PROVIDERS['BIGIP'])
    management_kwargs = dict(port=auth['port'], user=auth['user'], password=auth['password'])
    client = ManagementClient(auth['host'], **management_kwargs)
    kwargs = {}
    if version:
        kwargs['version'] = version
    extension_client = ExtensionClient(client, component, **kwargs)

    # intent based - support install in 'service' sub-command
    # install extension component if requested (and not installed)
    if install_component and not extension_client.package.is_installed()['installed']:
        extension_client.package.install()
        extension_client.service.is_available()

    if action == 'show':
        ctx.log(extension_client.service.show())
    elif action == 'create':
        ctx.log(_process_create(component, extension_client, declaration))
    elif action == 'delete':
        ctx.log(extension_client.service.delete())
    elif action == 'show-info':
        ctx.log(extension_client.service.show_info())
    elif action == 'show-failover':
        ctx.log(extension_client.service.show_trigger())
    elif action == 'trigger-failover':
        ctx.log(extension_client.service.trigger(
            config_file=utils_core.convert_to_absolute(declaration)))
    elif action == 'show-inspect':
        ctx.log(extension_client.service.show_inspect())
    elif action == 'reset':
        ctx.log(extension_client.service.reset(
            config_file=utils_core.convert_to_absolute(declaration)))
    else:
        raise click.ClickException('Action not implemented')


def _process_create(component, extension_client, declaration):
    if not extension_client.package.is_installed()['installed']:
        return ("Package is not installed, run command "
                "'f5 bigip extension package install --component %s'" % component)
    return extension_client.service.create(
        config_file=utils_core.convert_to_absolute(declaration))


click_repl.register_repl(cli)