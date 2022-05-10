import os

# If MFLOWGEN_ADK_NAME is set, this will use that for the adk.
# Otherwise, it will attempt to automatically detect which
# adk to use.
def get_sys_adk():
    adk_name = os.getenv('MFLOWGEN_ADK_NAME')
    
    if adk_name is None:
        if os.path.isdir('/gf'):
            adk_name = 'gf12-adk'
        elif os.path.isdir('/tsmc16'):
            adk_name = 'tsmc16'
        else:
            raise EnvironmentError('Set MFLOWGEN_ADK_NAME environment variable to name of adk you wish to use.')

    return adk_name
        
