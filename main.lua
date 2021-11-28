local mp = require("mp")
local msg = require("mp.msg")
local utils = require("mp.utils")

local IS_AUTO_START_ON = false
local ADDON_TOGGLE_KEYBIND = "F5"
local ADDON_VISIBILITY_TOGGLE_KEYBIND = "F6"
-- for Mac change python3 to python or pythonw
local PYTHON_COMMAND_NAME = "python3"
local PYTHON_SCRIPT_FILENAME = "interSubs.py"


local function put_cmd_in_bg(cmd) return cmd.." &" end

local function is_there_no_selected_subs()
	return mp.get_property("sub") == "no" or mp.get_property("sub") == "auto"
end

local python = {}

function python:start(ipc_file, subs_file)
	self.cmd = PYTHON_COMMAND_NAME..' "%s" --ipc-file-path="%s" --subs-file-path="%s"'
	self.script_file_path = utils.join_path(mp.get_script_directory(), PYTHON_SCRIPT_FILENAME)

	os.execute(put_cmd_in_bg(self.cmd:format(self.script_file_path, ipc_file, subs_file)))
end

function python:stop()
	os.execute(put_cmd_in_bg("pkill -f "..self.script_file_path))
end

local ipc = {}

function ipc:init()
	self.file_path = os.tmpname()
	mp.set_property("input-ipc-server", self.file_path)
end

function ipc:destroy()
	mp.set_property("input-ipc-server", "")
	os.remove(self.file_path)
end

local subs = {}

function subs:init()
	self:save_current_settings()
	self:hide_native_subs()

	self.file_path = os.tmpname()
	self.on_subs_change = function(_, text)
		if not text then return end
		local f = io.open(self.file_path, "w+")
		f:write(text)
		f:flush()
		f:close()
	end
	mp.observe_property("sub-text", "string", self.on_subs_change)
end

function subs:destroy()
	mp.unobserve_property(self.on_subs_change)
	os.remove(self.file_path)
	self:restore_settings()
end

function subs:save_current_settings()
	self.visibility = mp.get_property("sub-visibility")
	self.color = mp.get_property("sub-color", "1/1/1/1")
	self.border_color = mp.get_property("sub-border-color", "0/0/0/1")
	self.shadow_color = mp.get_property("sub-shadow-color", "0/0/0/1")
end

function subs:restore_settings()
	mp.set_property("sub-visibility", self.visibility)
	mp.set_property("sub-color", self.color)
	mp.set_property("sub-border-color", self.border_color)
	mp.set_property("sub-shadow-color", self.shadow_color)
end

function subs:hide_native_subs()
	mp.set_property("sub-visibility", "yes")
	mp.set_property("sub-ass-override", "force")

	mp.set_property("sub-color", "0/0/0/0")
	mp.set_property("sub-border-color", "0/0/0/0")
	mp.set_property("sub-shadow-color", "0/0/0/0")
end

local addon = {
	is_running = false,
	is_visible = true
}

function addon:stop()
	mp.osd_message("Quitting interSubs.")

	python:stop()
	ipc:destroy()
	subs:destroy()

	mp.unregister_event(addon.stop)
	self.is_running = false
end

function addon:start()
	if is_there_no_selected_subs() then
		mp.osd_message("Select subtitles before starting interSubs.")
		return
	end
	mp.osd_message("Starting interSubs.")

	subs:init()
	ipc:init()
	python:start(ipc.file_path, subs.file_path)

	mp.register_event("shutdown", addon.stop)
	self.is_running = true
end

local function toggle_addon_visibility()
	if not addon.is_running then return end
	msg.error("NotImplementedError")
end

local function toggle_addon_running_state()
	if addon.is_running then
		addon:stop()
	else
		addon:start()
	end
end

local function main()
	mp.add_forced_key_binding(ADDON_TOGGLE_KEYBIND, "start-stop-interSubs", toggle_addon_running_state)
	mp.add_forced_key_binding(ADDON_VISIBILITY_TOGGLE_KEYBIND, "hide-show-interSubs", toggle_addon_visibility)

	local auto_start = function()
		if is_there_no_selected_subs() then return end
		if IS_AUTO_START_ON and not addon.is_running then
			toggle_addon_running_state()
		end
	end
	mp.register_event("file-loaded", auto_start)
end

main()
