import sys
try:
    from wo.cli.main import WOTestApp
except ImportError:
    try:
        from wo.core.app import WOApp
    except ImportError:
        pass

def inspect_wo():
    import wo.cli.main
    app = wo.cli.main.WOApp()
    app.setup()
    
    print("Base Controller:", app.handler.get('controller', 'base'))
    print("Site Controller:", app.handler.get('controller', 'site'))
    
    for label in app.handler.list('controller'):
        print(f"Controller: {label}")

if __name__ == '__main__':
    inspect_wo()
