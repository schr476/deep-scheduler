import numpy as np
import concurrent.futures
from operator import itemgetter

from sim_objs import *
from sim_exp import arrival_rate_upperbound, slowdown
from rlearning import *

# ############################################  Scher  ########################################### #
class Scher(object):
  def __init__(self):
    pass
  
  def schedule(self, job, wload_l):
    return len(wload_l), None, None

# ###########################################  RLScher  ########################################## #
class RLScher(Scher):
  def __init__(self, sinfo_m, sching_m):
    self.sinfo_m = sinfo_m
    
    self.s_len = 6 # k, totaldemand, (load) min, max, mean, sigma
    self.N, self.T = sching_m['N'], sinfo_m['njob']
    
    self.learner = PolicyGradLearner(s_len=self.s_len, a_len=1, nn_len=10, w_actorcritic=False)
  
  def __repr__(self):
    return "RLScher[learner=\n{}]".format(self.learner)
  
  def n(self, job, wload_l):
    s = [job.k, job.totaldemand, min(wload_l), max(wload_l), np.mean(wload_l), np.std(wload_l) ]
    r = self.learner.get_action_val(s)
    if r < 1:
      r = 1
    elif r > len(wload_l):
      r = len(wload_l)
    return r*job.k
  
  def train(self):
    for i in range(45):
      alog(">> i= {}".format(i) )
      n_t_s_l, n_t_a_l, n_t_r_l = np.zeros((self.N, self.T, 1)), np.zeros((self.N, self.T, 1)), np.zeros((self.N, self.T, 1))
      for n in range(self.N):
        t_s_l, t_a_l, t_r_l = sample_traj(self.sinfo_m, self)
        alog("n= {}, avg_s= {}, avg_a= {}, avg_r= {}".format(n, np.mean(t_s_l), np.mean(t_a_l), np.mean(t_r_l) ) )
        n_t_s_l[n], n_t_a_l[n], n_t_r_l[n] = t_s_l, t_a_l, t_r_l
      self.learner.train_w_mult_trajs(n_t_s_l, n_t_a_l, n_t_r_l)
  
  def train_multithreaded(self, nsteps):
    if self.learner.restore(nsteps):
      log(WARNING, "learner.restore is a success, will not retrain.")
    else:
      tp = concurrent.futures.ThreadPoolExecutor(max_workers=100)
      for i in range(1, nsteps+1):
        alog(">> i= {}".format(i) )
        n_t_s_l, n_t_a_l, n_t_r_l = np.zeros((self.N, self.T, 1)), np.zeros((self.N, self.T, 1)), np.zeros((self.N, self.T, 1))
        future_n_m = {tp.submit(sample_traj, self.sinfo_m, self): n for n in range(self.N) }
        for future in concurrent.futures.as_completed(future_n_m):
          n = future_n_m[future]
          try:
            t_s_l, t_a_l, t_r_l = future.result()
          except Exception as exc:
            log(ERROR, "exception;", exc=exc)
          alog("n= {}, avg_s= {}, avg_a= {}, avg_r= {}".format(n, np.mean(t_s_l), np.mean(t_a_l), np.mean(t_r_l) ) )
          n_t_s_l[n], n_t_a_l[n], n_t_r_l[n] = t_s_l, t_a_l, t_r_l
        self.learner.train_w_mult_trajs(n_t_s_l, n_t_a_l, n_t_r_l)
        self.learner.save(i)
  
  def plot(self):
    load_l, Pr_bind_l = [], []
    for l in np.linspace(0, 1, 100):
      load_l.append(l)
      
      p = self.learner.get_action_dist([l] )[1]
      print("l= {}, p= {}".format(l, p) )
      Pr_bind_l.append(p)
    plot.plot(load_l, Pr_bind_l, color=NICE_RED, marker='.', linestyle=':', mew=2)
    
    # plot.legend()
    plot.xlabel('Worker load', fontsize=14)
    plot.ylabel('Probability of\nplacing an arrival', fontsize=14)
    # plot.title(r'$\mu= {}$, $r= {}$'.format(mu, r) )
    fig = plot.gcf()
    fig.set_size_inches(4, 3)
    plot.savefig('plot_rlscheduler.png', bbox_inches='tight')
    fig.clear()
    log(WARNING, "done.")

# ############################################  utils  ########################################### #
mapping_m = {'type': 'spreading'}
def sample_traj(sinfo_m, scher):
  def reward(slowdown):
    return 1/slowdown
  
  env = simpy.Environment()
  cl = Cluster(env, mapper=Mapper(mapping_m), scher=scher, **sinfo_m)
  jg = JobGen(env, out=cl, **sinfo_m)
  env.run(until=cl.wait_for_alljobs)
  
  T = sinfo_m['njob']
  t_s_l, t_a_l, t_r_l = np.zeros((T, scher.s_len)), np.zeros((T, 1)), np.zeros((T, 1))
  
  t = 0
  for jid, jinfo_m in sorted(cl.jid_info_m.iteritems(), key=itemgetter(0) ):
    blog(t=t, jid=jid, jinfo_m=jinfo_m)
    if jinfo_m['fate'] == 'finished':
      t_s_l[t, :] = jinfo_m['s']
      t_a_l[t, :] = jinfo_m['a']
      t_r_l[t, :] = reward(jinfo_m['runtime']/jinfo_m['expected_lifetime'] )
      t += 1
  return t_s_l, t_a_l, t_r_l

def evaluate(sinfo_m, scher):
  alog("scher= {}".format(scher) )
  for _ in range(3):
    t_s_l, t_a_l, t_r_l = sample_traj(sinfo_m, mapping_m, scher)
    print("avg_s= {}, avg_a= {}, avg_r= {}".format(np.mean(t_s_l), np.mean(t_a_l), np.mean(t_r_l) ) )

if __name__ == '__main__':
  sinfo_m = {
    'njob': 10000, 'nworker': 10, 'wcap': 10,
    'totaldemand_rv': TPareto(1, 10000, 1.1),
    'demandperslot_mean_rv': TPareto(0.1, 10, 1.1),
    'k_rv': DUniform(1, 1),
    'func_slowdown': slowdown}
  ar_ub = arrival_rate_upperbound(sinfo_m)
  sinfo_m['ar'] = 3/4*ar_ub
  sching_m = {'N': 10}
  blog(sinfo_m=sinfo_m, mapping_m=mapping_m, sching_m=sching_m)
  
  scher = RLScher(sinfo_m, sching_m)
  # sinfo_m['max_exprate'] = max_exprate
  # evaluate(sinfo_m, mapping_m, scher=Scher() )
  
  print("scher= {}".format(scher) )
  scher.train_multithreaded(40) # train()
  evaluate(sinfo_m, mapping_m, scher)
