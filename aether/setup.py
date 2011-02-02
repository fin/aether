from setuptools import setup

setup(name='aether',
      version='0.9',
      description='a simple way to share files in your local network',
      install_requires=['pynotify','twisted', 'pygtk', 'gtk', 'base64', 'json', 'pybonjour'],
      )
