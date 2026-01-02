/* extension.js — GNOME Wayland Backend for PyAutoGUI (GNOME >=45)
 *
 * D-Bus service: org.pyautogui.Wayland
 * Object path:  /org/pyautogui/Wayland
 *
 * Methods:
 *  - GetPosition()         -> (ii)
 *  - GetOutputs()          -> (s) JSON array of monitors [{x,y,width,height,scale}, ...]
 *  - GetKeyboardLayout()   -> (s) current keyboard layout ID (e.g. "xkb:fr::fra")
 *  - GetAuthTokenPath()    -> (s) path to this extension's authentication token file
 */
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Keyboard from 'resource:///org/gnome/shell/ui/status/keyboard.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';


/* --- Constants --- */

const IFACE_XML = `<node>
  <interface name="org.pyautogui.Wayland">
    <method name="GetPosition">
      <arg type="i" direction="out" name="x"/>
      <arg type="i" direction="out" name="y"/>
    </method>
    <method name="GetOutputs">
      <arg type="s" direction="out" name="json"/>
    </method>
    <method name="GetKeyboardLayout">
      <arg type="s" direction="out" name="layout"/>
    </method>
    <method name="GetAuthTokenPath">
      <arg type="s" direction="out" name="path"/>
    </method>
  </interface>
</node>`;


/* --- Global variables --- */

let _dbusImpl = null;
let _nameId = 0;


/* --- Internal functions --- */

function _loadAuthToken(authTokenPath) {
    try {
        const file = Gio.File.new_for_path(authTokenPath);
        const [success, contents] = file.load_contents(null);
        if (success) {
            const token = new TextDecoder().decode(contents).trim();
            log(`pyautogui-gnome-wayland: Token loaded successfully (length: ${token.length})`);
            return token;
        }
        throw new Error("Token file empty");
    } catch (e) {
        logError(e, 'pyautogui-gnome-wayland: Failed to load auth token');
        return null;
    }
}


/* --- DBus method implementations --- */

function GetPosition() {
    try {
        const [x, y] = global.get_pointer();
        return [x, y];
    } catch (e) {
        logError(e, 'pyautogui-gnome-wayland: GetPosition error');
        return [0, 0];
    }
}

function GetOutputs() {
    try {
        const monitors = [];
        const mons = Main.layoutManager ? Main.layoutManager.monitors : [];
        for (const m of mons) {
            monitors.push({
                x: m.x,
                y: m.y,
                width: m.width,
                height: m.height,
                scale: (m.scale_factor || 1.0)
            });
        }
        return JSON.stringify(monitors);
    } catch (e) {
        logError(e, 'pyautogui-gnome-wayland: GetOutputs error');
        return '[]';
    }
}

function GetKeyboardLayout() {
    try {
        const manager = Keyboard.getInputSourceManager();
        if (manager && manager.currentSource) {
            return manager.currentSource.id;
        }
        return "unknown";
    } catch (e) {
        logError(e, 'pyautogui-gnome-wayland: GetKeyboardLayout error');
        return "unknown";
    }
}


/* --- Exported extension class --- */

export default class PyAutoGUIExtension extends Extension {
    enable() {
        log('pyautogui-gnome-wayland: enable called');
        const authTokenPath = `${this.path}/auth_token`;

        /* Load auth token */
        this._authToken = _loadAuthToken(authTokenPath);
        if (!this._authToken) {
            logError('pyautogui-gnome-wayland: Cannot enable - no auth token');
            return;
        }
        log(`pyautogui-gnome-wayland: Auth token loaded: ${this._authToken.substring(0, 8)}...`);

        try {
            const nodeInfo = Gio.DBusNodeInfo.new_for_xml(IFACE_XML);
            const ifaceInfo = nodeInfo.interfaces[0];

            const vtable = {
                handle_method_call: (connection, sender, objectPath, interfaceName, methodName, parameters, invocation) => {
                    log(`pyautogui-gnome-wayland: Method called: ${methodName} from ${sender}`);

                    try {
                        if (methodName === 'GetAuthTokenPath') {
                            invocation.return_value(GLib.Variant.new('(s)', [authTokenPath]));
                            return;
                        }

                        if (!this._checkAuth(sender)) {
                            invocation.return_error_literal(
                                Gio.DBusError,
                                Gio.DBusError.ACCESS_DENIED,
                                'Authentication failed'
                            );
                            return;
                        }

                        let result;
                        switch (methodName) {
                            case 'GetPosition':
                                result = GetPosition();
                            invocation.return_value(GLib.Variant.new('(ii)', result));
                                break;
                            case 'GetOutputs':
                                result = GetOutputs();
                            invocation.return_value(GLib.Variant.new('(s)', [result]));
                                break;
                            case 'GetKeyboardLayout':
                                result = GetKeyboardLayout();
                            invocation.return_value(GLib.Variant.new('(s)', [result]));
                                break;
                            default:
                            invocation.return_error_literal(
                                Gio.DBusError,
                                Gio.DBusError.UNKNOWN_METHOD,
                                    `Method ${methodName} not found`
                            );
                        }

                    } catch (e) {
                        logError(e, `pyautogui-gnome-wayland: Error in ${methodName}`);
                        invocation.return_error_literal(
                            Gio.DBusError,
                            Gio.DBusError.FAILED,
                            e.message
                        );
                    }
                },
                handle_get_property: null,
                handle_set_property: null
            };

            _dbusImpl = Gio.DBus.session.register_object(
                '/org/pyautogui/Wayland',
                ifaceInfo,
                (connection, sender, objectPath, interfaceName, methodName, parameters, invocation) => {
                    vtable.handle_method_call(connection, sender, objectPath, interfaceName, methodName, parameters, invocation);
                },
                null,  /* get_property handler */
                null   /* set_property handler */
            );

            log(`pyautogui-gnome-wayland: DBus object registered with ID: ${_dbusImpl}`);

            /* Own the bus name */
            _nameId = Gio.DBus.session.own_name(
                'org.pyautogui.Wayland',
                Gio.BusNameOwnerFlags.NONE,
                () => {
                    log('pyautogui-gnome-wayland: DBus name ACQUIRED: org.pyautogui.Wayland');
                },
                () => {
                    log('pyautogui-gnome-wayland: DBus name LOST');
                }
            );

            log('pyautogui-gnome-wayland: enabled');
        } catch (e) {
            logError(e, 'pyautogui-gnome-wayland: enable failed');
            if (_dbusImpl) {
                try { Gio.DBus.session.unregister_object(_dbusImpl); } catch (e2) {}
                _dbusImpl = null;
            }
            if (_nameId) {
                try { Gio.DBus.session.unown_name(_nameId); } catch (e2) {}
                _nameId = 0;
            }
        }
    }

    _checkAuth(sender) {
        try {
            log(`pyautogui-gnome-wayland: checking auth for ${sender}`);

            if (!sender) {
                throw new Error('No sender information available');
            }

            if (sender.startsWith(':')) {
                try {
                    const result = Gio.DBus.session.call_sync(
                        'org.freedesktop.DBus',
                        '/org/freedesktop/DBus',
                        'org.freedesktop.DBus',
                        'ListNames',
                        null,
                        GLib.VariantType.new('(as)'),
                        Gio.DBusCallFlags.NONE,
                        -1,
                        null
                    );

                    const [names] = result.deep_unpack();

                    for (const name of names) {
                        if (name.startsWith('pyautogui.')) {
                            const ownerResult = Gio.DBus.session.call_sync(
                                'org.freedesktop.DBus',
                                '/org/freedesktop/DBus',
                                'org.freedesktop.DBus',
                                'GetNameOwner',
                                GLib.Variant.new('(s)', [name]),
                                GLib.VariantType.new('(s)'),
                                Gio.DBusCallFlags.NONE,
                                -1,
                                null
                            );

                            const [owner] = ownerResult.deep_unpack();
                            if (owner === sender) {
                                sender = name;
                                log(`pyautogui-gnome-wayland: Resolved ${owner} to ${name}`);
                                break;
                            }
                        }
                    }
                } catch (e) {
                    logError(e, 'pyautogui-gnome-wayland: Failed to resolve sender name');
                    return false;
                }
            }

            const parts = sender.split('.');

            if (parts.length !== 2 ||
                parts[0] !== 'pyautogui') {
                log(`pyautogui-gnome-wayland: Invalid sender format: ${sender}`);
                return false;
            }

            const senderToken = parts[1];

            if (senderToken !== this._authToken) {
                log(`pyautogui-gnome-wayland: Token mismatch`);
                return false;
            }

            log(`pyautogui-gnome-wayland: Authentication successful for ${sender}`);
            return true;

        } catch (e) {
            logError(e, 'pyautogui-gnome-wayland: Authentication check failed');
            return false;
        }
    }

    disable() {
        log('pyautogui-gnome-wayland: disable called');

        if (_dbusImpl) {
            try {
                Gio.DBus.session.unregister_object(_dbusImpl);
            } catch (e) {
                logError(e, 'pyautogui-gnome-wayland: unregister_object error');
            }
            _dbusImpl = null;
        }

        if (_nameId) {
            try {
                Gio.DBus.session.unown_name(_nameId);
            } catch (e) {
                logError(e, 'pyautogui-gnome-wayland: unown_name error');
            }
            _nameId = 0;
        }

        this._authToken = null;

        log('pyautogui-gnome-wayland: disabled');
    }
}

