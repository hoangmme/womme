from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController
import downloaded_womme

class Base(CementBaseController):
    class Meta:
        label = 'base'

class Site(CementBaseController):
    class Meta:
        label = 'site'
        stacked_on = 'base'
        stacked_type = 'nested'

class MyApp(CementApp):
    class Meta:
        label = 'wo'
        base_controller = Base

app = MyApp()
app.setup()
app.handler.register(Site)
try:
    downloaded_womme.load(app)
    print("LOADED OK")
except Exception as e:
    import traceback
    traceback.print_exc()
