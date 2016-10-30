#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Written by Jason K. MacDuffie
# Encrypt files with ccrypt in Caja
import os
import subprocess
import urllib
import subprocess

from gi.repository import Caja, GObject, Gio
from locale import getlocale

CCRYPT_SCHEMA = 'org.mate.applications-ccrypt'

# No clue what the right way to do locales is, so this is my best attempt
loc = getlocale()[0]
encrypt_loc = {
    'en': 'Encrypt',
    'eo': 'Ĉifri'
}
decrypt_loc = {
    'en': 'Decrypt',
    'eo': 'Deĉifri'
}

def call_ccdecrypt(filename):
    zenity_prompt = [
        'zenity',
        '--entry',
        '--hide-text',
        '--title="Decryption Key"',
        '--text="Enter a key for ccdecrypt:"'
    ]
    prompt_process = subprocess.Popen(zenity_prompt, stdout=subprocess.PIPE)
    decrypt_process = subprocess.Popen(['ccdecrypt', '-k', '-', filename],
                                       stdin=prompt_process.stdout)
    prompt_process.wait()
    decrypt_process.wait()

    # Check if all went well
    if decrypt_process.returncode != 0:
        zenity_error_process = subprocess.Popen([
            'zenity',
            '--error',
            '--title="Decryption Key"',
            '--text="Decryption failed. The entered key may have been incorrect."'
        ])

        return 'Failure'
    
    return 'Success'

def call_ccencrypt(filename):
    zenity_prompt1 = [
        'zenity',
        '--entry',
        '--hide-text',
        '--title="Encryption Key"',
        '--text="Enter a key for ccencrypt:"'
    ]
    zenity_prompt2 = [
        'zenity',
        '--entry',
        '--hide-text',
        '--title="Encryption key"',
        '--text="Enter the same key again to confirm:"'
    ]
    prompt1_proc = subprocess.Popen(zenity_prompt1, stdout=subprocess.PIPE)
    prompt1_output = prompt1_proc.communicate()[0]
    prompt2_proc = subprocess.Popen(zenity_prompt2, stdout=subprocess.PIPE)
    prompt2_output = prompt2_proc.communicate()[0]

    if prompt1_output != prompt2_output:
        mismatch_notify = subprocess.Popen([
            'zenity',
            '--error',
            '--title="Encryption Key',
            '--text="The encryption keys did not match."'
        ])

        return 'Failure'

    encrypt_process = subprocess.Popen(['ccencrypt', '-k', '-', filename],
                                       stdin=subprocess.PIPE)
    encrypt_process.communicate(input=prompt2_output)

    # Check if all went well
    if encrypt_process.returncode != 0:
        zenity_error_process = subprocess.Popen([
            'zenity',
            '--error',
            '--title="Encryption Key"',
            '--text="Encryption failed for some reason."'
        ])
        
        return 'Failure'
    
    return 'Success'

class CCryptExtension(Caja.MenuProvider, GObject.GObject):
    def __init__(self):
        pass

    def _ccencrypt_file(self, file):
        filename = urllib.unquote(file.get_uri()[7:])
        call_ccencrypt(filename)

    def _ccdecrypt_file(self, file):
        filename = urllib.unquote(file.get_uri()[7:])
        call_ccdecrypt(filename)

    def menu_activate_encryption(self, menu, file):
        self._ccencrypt_file(file)

    def menu_activate_decryption(self, menu, file):
        self._ccdecrypt_file(file)

    def get_file_items(self, window, files):
        if len(files) != 1:
            return

        file = files[0]
        filename = file.get_name()

        if file.is_directory() or file.get_uri_scheme() != 'file':
            return

        encryption_item = Caja.MenuItem(name='CajaPython::ccencrypt_file_item',
                                        label=encrypt_loc.get(loc,'Encrypt') + '...',
                                        tip='Encrypt this file using ccencrypt')

        encryption_item.connect('activate', self.menu_activate_encryption, file)

        # Check if file is .cpt or otherwise
        is_encrypted = file.get_name().endswith('.cpt')

        if not is_encrypted:
            return encryption_item,

        # Otherwise, include a decryption option
        decryption_item = Caja.MenuItem(name='CajaPython::ccdecrypt_file_item',
                                        label=decrypt_loc.get(loc,'Decrypt') + '...',
                                        tip='Decrypt this file using ccdecrypt')

        decryption_item.connect('activate', self.menu_activate_decryption, file)

        return (encryption_item, decryption_item)

