#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
root = '/dev/shm/'


def fyi(text):
    print '    ' + text


def info(text):
    print '>>> ' + text


def get_config():
    from configobj import ConfigObj
    config_filename = os.path.join(os.getenv('HOME'), '.config',
                                   'drupebox')
    if not path_exists(config_filename):
        config = ConfigObj()
        config.filename = config_filename
        import dropbox

        # Get your app key and secret from the Dropbox developer website

        app_key = '1skff241na3x0at'
        app_secret = 'srd8w4mvppiq9vg'

        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key,
                app_secret)
        authorize_url = flow.start()
        print '1. Go to: ' + authorize_url
        print '2. Click "Allow" (you might have to log in first)'
        print '3. Copy the authorization code.'
        code = raw_input('Enter the authorization code here: ').strip()
        (config['access_token'], config['user_id']) = flow.finish(code)
        config['dropbox_local_path'] = \
            raw_input('Enter dropbox local path (or press enter for '
                      + os.path.join(os.getenv('HOME'), 'Dropbox')
                      + '/) ').strip()
        if config['dropbox_local_path'] == '':
            config['dropbox_local_path'] = os.path.join(os.getenv('HOME'
                    ), 'Dropbox') + '/'
        config['max_file_size'] = 10000000
        config.write()

    config = ConfigObj(config_filename)
    return config


def xconfig():
    if xconfig.location == '':
        xconfig.location = get_config()
    return xconfig.location


xconfig.location = ''


def dump(text, name):
    text = str(text)
    with open(root + name, 'wb') as f:
        f.write(text)


def get_tree():
    tree = []
    for (root, dirs, files) in os.walk(xconfig()['dropbox_local_path'],
            topdown=True, followlinks=True):
        for name in files:
            tree.append(os.path.join(root, name))
        for name in dirs:
            tree.append(os.path.join(root, name))
    return tree


def store_tree(tree):
    tree = '\n'.join(tree)
    dump(tree, 'treeStore')


def load_tree():
    try:
        last_tree = file(root + 'treeStore', 'r').read()
    except:
        last_tree = ''
    last_tree = last_tree.split('\n')

    return last_tree


def determine_deleted_files(tree_now, tree_last):
    deleted = []
    if tree_last == ['']:
        return []
    for element in tree_last:
        if not element in tree_now:
            deleted.append(element)
    return deleted


def upload(client, local_file_path, remote_file_path):
    print 'uuu', local_file_path
    f = open(local_file_path, 'rb')
    response = client.put_file(remote_file_path, f, overwrite=True)


def download(client, remote_file_path, local_file_path):
    print 'ddd', remote_file_path
    (f, metadata) = client.get_file_and_metadata(remote_file_path)
    out = open(local_file_path, 'wb')
    out.write(f.read())
    out.close()


    # print metadata

def unnice(timer):
    return time.mktime(datetime.strptime(timer,
                       '%a, %d %b %Y %H:%M:%S +0000').timetuple())


unix_time = unnice


def nice(timepoint):
    return datetime.fromtimestamp(float(timepoint)).strftime('%a, %d %b %Y %H:%M:%S +0000'
            )


readable_time = nice


def path_exists(path):
    try:
        os.stat(path)
        return True
    except:
        return False


def local_item_modified_time(local_file_path):
    return os.path.getmtime(local_file_path)


def fix_local_time(client, remote_file_path):
    remote_path = remote_file_path
    extra_path = '/'.join(remote_path.split('/')[0:-1])
    info('fix local time on ' + remote_file_path)

    tmp_folder = client.metadata('/' + extra_path)['contents']
    for tmp_item in tmp_folder:
        if tmp_item['path'] == remote_path:
            break  # found it
    tmp_time = tmp_item['modified']
    os.utime(xconfig()['dropbox_local_path'] + remote_path,
             (int(unnice(tmp_time)), int(unnice(tmp_time))))


def skip(local_file_path):
    local_item = local_file_path.split('/')[-1]
    if local_item[0:len('.fuse_hidden')] == '.fuse_hidden':
        print 'ignore fuse hidden files'
        return True
    else:
        try:
            local_time = local_item_modified_time(local_file_path)
        except:
            print 'crash on local time check on', local_item
            return True
        return False


def local_item_not_found_at_remote(remote_folder, remote_file_path):
    remote_path = remote_file_path
    extra_path = '/'.join(remote_path.split('/')[0:-1])
    remote_folder_path = extra_path

    # remote_folder = client.metadata('/'+remote_folder_path)['contents']

    unnaccounted_local_file = True
    for tmp_item in remote_folder:
        if tmp_item['path'] == remote_file_path:
            unnaccounted_local_file = False
    return unnaccounted_local_file


def remote_item_modified(client, remote_file_path):
    remote_path = remote_file_path
    extra_path = '/'.join(remote_path.split('/')[0:-1])
    remote_folder_path = extra_path
    remote_folder_with_deleted = client.metadata('/'
            + remote_folder_path, include_deleted=True)['contents']
    folder_with_deleted = remote_folder_with_deleted
    remote_time = 0
    for unn_item in folder_with_deleted:
        if unn_item['path'] == remote_file_path:
            if 'is_deleted' in unn_item and unn_item['is_deleted'] \
                == True:
                remote_time = unnice(unn_item['modified'])
                break
    return remote_time


