import deluge.ui.webui.lib.newforms_plus as forms
from deluge.ui.client import client
from deluge import component
from deluge.log import LOG as log

import ui

PREVENT_WHEN_LIST = [
     _("Downloading"),
     _("Downloading or Seeding"),
     _("Always")
]

class PreventSuspendCfgForm(forms.Form):
    title = _("Prevent Suspend")

    def initial_data(self):
        data = sclient.preventsuspend_get_config()
        return data

    def save(self, data):
        cfg = dict(data)
        sclient.preventsuspend_set_config(cfg)

    #input fields:
    enabled = forms.CheckBox(_('Enable suspend prevention'))
    preventwhen = forms.IntChoiceField(label=_("Prevent when"),
                                    choices=enumerate(PREVENT_WHEN_LIST))

class WebUI(WebPluginBase):
   def enable(self):
       log.debug("**ENABLING prevent suspend webui plugin**")
       component.get("ConfigPageManager").register('plugins',
                                                   'preventsuspend',
                                                   PreventSuspendCfgForm)

   def disable(self):
       component.get("ConfigPageManager").deregister('preventsuspend')
        
