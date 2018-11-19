from modeling import *

# def ar_for_ro(ro, N, Cap, k, D, S):
#   return ro*N*Cap/k.mean()/D.mean()/S.mean()

def ar_for_ro(ro, N, Cap, k, R, L, S):
  return ro*N*Cap/k.mean()/R.mean()/L.mean()/S.mean()

def EW_MMc(ar, EX, c):
  ro = ar*EX/c
  C = 1/(1 + (1-ro)*G(c+1)/(c*ro)**c * sum([(c*ro)**k/G(k+1) for k in range(c) ] ) )
  # EN = ro/(1-ro)*C + c*ro
  return C/(c/EX - ar)

def EW_MGc(ar, X, c):
  EX2, EX = X.moment(2), X.moment(1)
  CoeffVar = math.sqrt(EX2 - EX**2)/EX
  return (1 + CoeffVar**2)/2 * EW_MMc(ar, EX, c)

def check_MGc_assumption():
  # N, Cap = 10, 1
  N_times_Cap = 100
  r = 1
  L = Exp(1, 1)
  S = DUniform(1, 1)
  sinfo_m['njob'] = 2000*20
  sching_m = {'type': 'plain', 'r': r}
  blog(N_times_Cap=N_times_Cap, sinfo_m=sinfo_m, mapping_m=mapping_m, sching_m=sching_m)
  
  def run(ro, N, R, L, S):
    Cap = int(N_times_Cap/N)
    print("\n")
    log(INFO, "ro= {}, N= {}, Cap= {}, R= {}, L= {}".format(ro, N, Cap, R, L) )
    
    ar = round(ar_for_ro(ro, N, Cap, k, R, L, S), 2)
    sinfo_m.update({
      'nworker': N, 'wcap': Cap, 'ar': ar,
      'reqed_rv': R,
      'lifetime_rv': L,
      'straggle_m': {'slowdown': lambda load: S.sample() } } )
    sim_m = sim(sinfo_m, mapping_m, sching_m, "N{}_C{}".format(N, Cap) )
    blog(sim_m=sim_m)
    
    c = int(N*Cap/R.mean() ) # N*Cap
    print("c= {}".format(c) )
    EW = EW_MGc(ar, L, c)
    sim_EW = sim_m['waittime_mean']
    print("sim_EW= {}, M/G/c_EW= {}".format(sim_EW, EW) )
    return sim_EW
  
  def test(ro, R=DUniform(1, 1) ):
    print("---------------")
    run(ro, 1, R, L, S)
    # run(ro, 2, R, L, S)
    # run(ro, 5, R, L, S)
    # run(ro, 10, R, L, S)
  
  def check_EW_scaling_wrt_ro(N, R):
    log(INFO, "", N=N, R=R)
    
    # '''
    ro_l, EW_l = [], []
    for ro in np.linspace(0.1, 0.9, 9):
      ro = round(ro, 2)
      EW = run(ro, N, R, L, S)
      print("ro= {}, EW= {}".format(ro, EW) )
      
      ro_l.append(ro)
      EW_l.append(EW)
    blog(ro_l=ro_l, EW_l=EW_l)
    # '''
    
    # ro_l= [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    # EW_l= [0.00025548087470978202, 0.00056689800613990546, 0.00089200542402208672, 0.0012637166320921696, 0.0017178514022176334, 0.0021802843452227629, 0.002912705863562876, 0.0061096923858674568, 0.043253547318583753]
    print("ratio = EW/(ro/(1-ro))")
    for i, EW in enumerate(EW_l):
      ro = ro_l[i]
      ratio = EW/(ro/(1-ro) )
      print("ro= {}, ratio= {}".format(ro, ratio) )
    log(INFO, "done.")
  
  def check_EW_scaling_wrt_EL2_over_EL(N, R, ro):
    log(INFO, "", N=N, R=R, ro=ro)
    
    EL2_over_EL_l, EW_l = [], []
    for mu in np.linspace(0.1, 1, 10):
      L = Exp(mu, 1)
      EL2_over_EL = round(L.moment(2)/L.moment(1), 2)
      EW = run(ro, N, R, L, S)
      print("EL2_over_EL= {}, EW= {}".format(EL2_over_EL, EW) )
      
      EL2_over_EL_l.append(EL2_over_EL)
      EW_l.append(EW)
    blog(EL2_over_EL_l=EL2_over_EL_l, EW_l=EW_l)
    # '''
    
    print("ratio = EW/(EL2/EL)")
    for i, EW in enumerate(EW_l):
      EL2_over_EL = EL2_over_EL_l[i]
      ratio = EW/EL2_over_EL
      print("EL2_over_EL= {}, ratio= {}".format(EL2_over_EL, ratio) )
    log(INFO, "done.")
  
  def check_EW_scaling_wrt_ER2_over_ER(N, L, ro):
    log(INFO, "", N=N, L=L, ro=ro)
    
    ER2_over_ER_l, EW_l = [], []
    for u in np.linspace(0.1, 1, 10):
      R = Uniform(0.1, u)
      ER2_over_ER = round(R.moment(2)/R.moment(1), 2)
      EW = run(ro, N, R, L, S)
      print("ER2_over_ER= {}, EW= {}".format(ER2_over_ER, EW) )
      
      ER2_over_ER_l.append(ER2_over_ER)
      EW_l.append(EW)
    blog(ER2_over_ER_l=ER2_over_ER_l, EW_l=EW_l)
    
    print("ratio = EW/(ER2/ER)")
    for i, EW in enumerate(EW_l):
      ER2_over_ER = ER2_over_ER_l[i]
      ratio = EW/ER2_over_ER
      print("ER2_over_ER= {}, ratio= {}".format(ER2_over_ER, ratio) )
    log(INFO, "done.")
  
  def check_EW_scaling_wrt_Ek2_over_Ek(N, R, L, ro):
    log(INFO, "", N=N, R=R, L=L, ro=ro)
    
    Ek2_over_Ek_l, EW_l = [], []
    for u in range(1, 10):
      k = DUniform(1, u)
      Ek2_over_Ek = round(k.moment(2)/k.moment(1), 2)
      EW = run(ro, N, R, L, S)
      print("Ek2_over_Ek= {}, EW= {}".format(Ek2_over_Ek, EW) )
      
      Ek2_over_Ek_l.append(Ek2_over_Ek)
      EW_l.append(EW)
    blog(Ek2_over_Ek_l=Ek2_over_Ek_l, EW_l=EW_l)
    
    print("ratio = EW/(ER2/ER)")
    for i, EW in enumerate(EW_l):
      Ek2_over_Ek = Ek2_over_Ek_l[i]
      ratio = EW/Ek2_over_Ek
      print("Ek2_over_Ek= {}, ratio= {}".format(Ek2_over_Ek, ratio) )
    log(INFO, "done.")
  
  def check_EW_scaling_wrt_model(N, k, R, L, S):
    log(INFO, "", N=N, k=k, R=R, L=L, S=S)
    
    def model(ro):
      return ro/(1-ro) \
             * k.moment(2)*R.moment(2)*L.moment(2)*S.moment(2) \
             / (k.moment(1)*R.moment(1)*L.moment(1)*S.moment(1) ) / 2
    
    model_l, EW_l = [], []
    for ro in np.linspace(0.1, 0.9, 9):
      ro = round(ro, 2)
      m = model(ro)
      EW = run(ro, N, R, L, S)
      print("m= {}, EW= {}".format(m, EW) )
      
      model_l.append(m)
      EW_l.append(EW)
    blog(model_l=model_l, EW_l=EW_l)
    
    print("ratio = EW/model")
    for i, EW in enumerate(EW_l):
      m = model_l[i]
      ratio = EW/m
      print("model= {}, ratio= {}".format(m, ratio) )
    log(INFO, "done.")
  
  # test(ro=0.4)
  # test(ro=0.65)
  # test(ro=0.9)
  
  # R = Uniform(0.25, 0.75) # Uniform(0.5, 1.5)
  # test(0.9, R)
  
  # R = Uniform(0.25, 0.75) # Uniform(1, 1) # Uniform(0.05, 0.15) # Uniform(0.5, 1.5)
  # check_EW_scaling_wrt_ro(5, R)
  
  # R = Uniform(1.5, 2.5) # Uniform(2, 2)
  # check_EW_scaling_wrt_EL2_over_EL(N, R, ro=0.85)
  
  # L = Exp(0.1, 1)
  # check_EW_scaling_wrt_ER2_over_ER(N, L, ro=0.85)
  
  # R = Uniform(1, 1) # Uniform(1, 1)
  # L = Exp(0.1, 1) # Uniform(1, 1)
  # check_EW_scaling_wrt_Ek2_over_Ek(N, R, L, ro=0.85)
  
  k = DUniform(1, 4)
  R = Uniform(1, 1) # Uniform(1, 1)
  L = Exp(0.1, 1) # Uniform(1, 1)
  S = Uniform(1, 4)
  check_EW_scaling_wrt_model(N, k, R, L, S)
  
  log(INFO, "done.")

if __name__ == "__main__":
  N, Cap = 10, 1
  b, beta = 10, 5
  a, alpha = 1, 1000 # 2
  k = BZipf(1, 1)
  r = 1
  log(INFO, "", k=k, r=r, b=b, beta=beta, a=a, alpha=alpha)
  def alpha_gen(ro):
    return alpha
  S = Pareto(a, alpha)
  ar = round(ar_for_ro_pareto(1/2, N, Cap, k, b, beta, a, alpha_gen), 2)
  
  sinfo_m = {
    'ar': ar, 'njob': 2000*10, 'nworker': N, 'wcap': Cap,
    'lifetime_rv': Pareto(b, beta),
    'reqed_rv': DUniform(1, 1),
    'k_rv': k,
    'straggle_m': {'slowdown': lambda load: S.sample() } }
  mapping_m = {'type': 'spreading'}
  sching_m = {'type': 'expand_if_totaldemand_leq', 'r': r, 'threshold': None}
  # blog(sinfo_m=sinfo_m, mapping_m=mapping_m, sching_m=sching_m)
  
  check_MGc_assumption()