from dp import dynaplex

def GetDCLPolicy(mdp, gen):
    dcl_filename = f'dcl_policy_gen{gen}'
    dcl_load_path = dynaplex.filepath(mdp.identifier(), dcl_filename)
    return dynaplex.load_policy(mdp, dcl_load_path)
def GetPPOPolicy(mdp):
    ppo_filename = 'ppo_policy'
    ppo_load_path = dynaplex.filepath(mdp.identifier(), "policies", ppo_filename)
    return dynaplex.load_policy(mdp, ppo_load_path)