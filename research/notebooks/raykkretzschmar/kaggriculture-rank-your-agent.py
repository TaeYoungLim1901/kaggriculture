import subprocess, sys
from importlib.metadata import PackageNotFoundError, version as pkg_version

ENGINE_VERSION = "1.32.3"   # the version these reference agents were measured on


def installed_engine():
    try:
        return pkg_version("kaggle-environments")
    except PackageNotFoundError:
        return None


def ensure_engine(want=ENGINE_VERSION):
    have = installed_engine()
    if have != want:
        print(f"installing kaggle-environments=={want} (found: {have})")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", f"kaggle-environments=={want}"],
            check=False,
        )
        for mod in [m for m in list(sys.modules) if m.startswith("kaggle_environments")]:
            del sys.modules[mod]
        have = installed_engine()
    return have


actual = ensure_engine()
print("kaggle-environments (reported):", actual)

from kaggle_environments import make
make("kaggriculture", configuration={"episodeSteps": 24})
print("kaggriculture environment loads OK")


import importlib.util, itertools, json, math, os, shutil, sys, tarfile, time, zipfile
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 90)

def find_dataset():
    """Locate the reference-agent dataset.

    Prefers the canonical mount, but falls back to scanning /kaggle/input for the
    manifest so a renamed or forked copy still works.
    """
    root = Path("/kaggle/input")
    # Kaggle has two input layouts depending on the image: the older flat
    # /kaggle/input/SLUG and the newer /kaggle/input/datasets/OWNER/SLUG.
    # Try both, then fall back to searching for the manifest.
    for candidate in (root / "kaggriculture-reference-agents", root / "datasets" / "raykkretzschmar/kaggriculture-reference-agents"):
        if (candidate / "agents_manifest.csv").exists():
            return candidate
    for hit in sorted(root.rglob("agents_manifest.csv")):
        return hit.parent
    raise SystemExit(
        "Reference-agent dataset not attached.\n"
        "Add Input -> Datasets -> search 'Kaggriculture Reference Agents', then re-run."
    )


DATASET_DIR = find_dataset()
print("dataset:", DATASET_DIR)
print("contents:", sorted(p.name for p in DATASET_DIR.iterdir()))


# Behavioural engine check. The version string can lie -- a pip install writes new
# package metadata while `import kaggle_environments` may still resolve to an older copy
# earlier on sys.path. So replay a real game out of the dataset and require the banks to
# match. Expected values are read from the CSV, so this stays correct if the dataset is
# ever re-measured.
def _fixture_agent(path, name):
    spec = importlib.util.spec_from_file_location(f"fixture_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def verify_engine_behaviour():
    """Replay one recorded pairing; return (ok, detail)."""
    games = pd.read_csv(DATASET_DIR / "head_to_head_games.csv")
    row = games.iloc[0]
    a = _fixture_agent(DATASET_DIR / f"{row.agent_a}.py", "a")
    b = _fixture_agent(DATASET_DIR / f"{row.agent_b}.py", "b")
    seat = int(row.seat_of_a)
    pair = [a, b] if seat == 0 else [b, a]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": int(row.seed)}, debug=False)
    env.run(pair)
    rewards = [step.reward for step in env.steps[-1]]
    got_a, got_b = round(rewards[seat]), round(rewards[1 - seat])
    ok = (got_a == int(row.bank_a)) and (got_b == int(row.bank_b))
    return ok, (f"{row.agent_a} vs {row.agent_b}, seed {row.seed}, seat {seat}: "
                f"expected {int(row.bank_a):,}/{int(row.bank_b):,}, got {got_a:,}/{got_b:,}")


_ok, _detail = verify_engine_behaviour()
print(("PASS  " if _ok else "FAIL  ") + _detail)
if not _ok:
    raise SystemExit(
        "The engine is not behaving like the one the dataset was measured on "
        f"({ENGINE_VERSION}), whatever version string it reports.\n"
        "Every bank, margin and expected_bank below would be measured in a different "
        "game than the one documented. Restart the session after installing "
        f"kaggle-environments=={ENGINE_VERSION}, or re-measure the ladder yourself."
    )


manifest = pd.read_csv(DATASET_DIR / "agents_manifest.csv").sort_values("tier")
manifest[["tier", "agent_name", "headline", "expected_bank",
          "hands", "extra_quadrants", "crops", "animals"]].to_string(index=False)


for _, row in manifest.iterrows():
    print(f"--- tier {row.tier}: {row.agent_name} " + "-" * (52 - len(str(row.agent_name))))
    print("  strategy:", row.strategy)
    print("  lesson  :", row.lesson)
    print()


curves = pd.read_csv(DATASET_DIR / "price_curves.csv")
curves.sort_values("base_price", ascending=False).to_string(index=False)


# Same thing as a picture: revenue you can actually extract per product.
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.6))

sold = [50, 150, 400, 1000]
for _, r in curves.iterrows():
    prices = [r.price_at_50_sold, r.price_at_150_sold,
              r.price_at_400_sold, r.price_at_1000_sold]
    style = "-o" if r.glut_target >= 1.0 else "--s"
    ax1.plot(sold, prices, style, label=f"{r['product']} ({r.glut_shape})", alpha=.85)
ax1.set_xscale("log")
ax1.set_xlabel("net units sold into the market")
ax1.set_ylabel("price per unit ($)")
ax1.set_title("Price decay by product\n(solid = collapses under one field's output)")
ax1.legend(fontsize=7, ncol=2)
ax1.grid(alpha=.3)

# Cumulative revenue if you sold N units, at the price after N units.
for _, r in curves.iterrows():
    rev = [n * p for n, p in zip(sold, [r.price_at_50_sold, r.price_at_150_sold,
                                        r.price_at_400_sold, r.price_at_1000_sold])]
    ax2.plot(sold, rev, "-o", label=r["product"], alpha=.85)
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("net units sold")
ax2.set_ylabel("gross revenue at that price ($)")
ax2.set_title("Where the money actually is")
ax2.legend(fontsize=7, ncol=2)
ax2.grid(alpha=.3)

plt.tight_layout(); plt.show()


def load_agent(path, name=None):
    """Import a single-file Kaggriculture agent and return its `agent` callable."""
    path = Path(path)
    name = name or path.stem
    spec = importlib.util.spec_from_file_location(f"kagri_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "agent"):
        raise AttributeError(f"{path} defines no `agent` function")
    return module.agent


reference = {}
for _, row in manifest.iterrows():
    reference[row.agent_slug] = load_agent(DATASET_DIR / row.file, row.agent_slug)

TIER_OF = dict(zip(manifest.agent_slug, manifest.tier))
NAME_OF = dict(zip(manifest.agent_slug, manifest.agent_name))
print(f"loaded {len(reference)} reference agents:",
      ", ".join(f"{s} (t{TIER_OF[s]})" for s in reference))


def find_top_meta():
    """Locate the top-meta agent from the attached notebook output, if present."""
    root = Path("/kaggle/input")
    if not root.exists():
        return None
    for candidate in (root / "kaggriculture-findings-from-zero-to-top-meta" / "main.py",
                      root / "kernels" / "raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta" / "main.py"):
        if candidate.exists():
            return candidate
    # Fall back to any attached main.py that carries the tape the agent is built on.
    for hit in sorted(root.rglob("main.py")):
        try:
            head = hit.read_text(errors="ignore")[:4000]
        except OSError:
            continue
        if "_ACTIONS" in head and "b85decode" in head:
            return hit
    return None


TOP_META_PATH = find_top_meta()
TOP_META_SLUG = "top_meta_host"
if TOP_META_PATH is None:
    top_meta = None
    print("top-meta host not attached -- skipping it. Add Input -> Notebook Output ->")
    print("  raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta")
else:
    top_meta = load_agent(TOP_META_PATH, TOP_META_SLUG)
    TIER_OF[TOP_META_SLUG] = 10
    NAME_OF[TOP_META_SLUG] = "Top Meta Host"
    print(f"top-meta host: {TOP_META_PATH} ({TOP_META_PATH.stat().st_size:,} bytes)")


# Build the candidate, so you can re-run the experiment yourself.
#
# Every shipped agent exposes `act(obs, policy)` -- the scheduler and the policy are
# separate -- so a new agent is a dict, not a new file. This is the cheapest way to
# test a production idea in this game.
import copy

spec = importlib.util.spec_from_file_location("rita_mod", DATASET_DIR / "rancher_rita.py")
rita_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rita_mod)

DROVER = copy.deepcopy(rita_mod.POLICY)          # Rita's plan...
DROVER["build"] = [{"kind": "PASTURE", "target": 16, "share": 0.5,
                    "from_day": 0, "until_day": 20}]
DROVER["animals"] = ["COW"]                       # ...with the sheep leg replaced
DROVER["animal_target"] = {"COW": 16}             #    by four more cows
DROVER["sell_order"] = ["MILK", "WHEAT"]

drover = lambda obs: rita_mod.act(obs, DROVER)
rita = lambda obs: rita_mod.act(obs, rita_mod.POLICY)


def quick_duel(a, b, seeds):
    """Minimal seat-swapped comparison. Self-contained so this section can be read
    and run on its own, before the full harness further down."""
    wins = losses = 0
    margins = []
    for seed in seeds:
        for seat in (0, 1):
            pair = [a, b] if seat == 0 else [b, a]
            env = make("kaggriculture",
                       configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run(pair)
            r = [s.reward for s in env.steps[-1]]
            x, y = r[seat], r[1 - seat]
            if x is None or y is None:
                continue
            margins.append(x - y)
            wins += x > y
            losses += x < y
    return wins, losses, sum(margins) / len(margins)


# Tuning seeds say the all-cow build is better. Held-out seeds disagree.
for label, seed_set in (("tuned-on  (7000-7002)", [7000, 7001, 7002]),
                        ("held-out  (8000-8002)", [8000, 8001, 8002])):
    w, l, margin = quick_duel(drover, rita, seed_set)
    verdict = "candidate wins" if w > l else "Rita wins"
    print(f"{label}:  {w}-{l}  margin {margin:+,.0f}   -> {verdict}")


import base64, hashlib, io, tarfile, tempfile, zlib

WORK = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path(".")
TEMP = Path(tempfile.mkdtemp(prefix="rank-your-agent-"))
SUBMISSION_B85 = 'c-rlJ*OKDOvgrGK1vF+0Xy!;r!Yr%+;gRreVh{oZ2!sSOc=+}!2MrB9Gi&X=PsEKl{V)SnSy@@>Dl03Cx3{+z<oDK6sJ9|AOIBHyX>q~GC59ebCW2@w($lHPjucK-MCSY3+uJvGxe`R#GNdKOk6gcvgw_7~c`gb3_49#ahu^+^qp(yXPZD)YRPX)H3G`S3w9fBiW+W_EA|pwFf%5w>h-!^v2Kd*=yWa6+tOo{AXT8#OI`$kkn|B8naz4KJvRSEHY_ZS?UYtPRB7`~`xk2r6C`ZP@jK2wPDl1@k#zY+K0rJ4jo!fP+i^Ob0C>b4~4(u?fE*ecd(oVGoQ~bQo1fzVSxa=y9Xss7ejzv*8pNP6RXWSh!8IFeLz_EgRQ`QRtOa*Vlv5rqbEEwhD8Rx!zIC9jS-MZOhb&3@yJWf*LrhDqw%1F7J80X^0!3CC`8OR?}q%eqzRH1|RE3>)7<D|03fMYeDdwX`;PQ}+g&y0zKHm?#N5ACU9vRvqsWYC+jb3+fAIotMa#GbULCy8COHJK!noR14L=U`>kV1=pDQ>sHMc9Ln%nPYHx02LM$m%9aaM9LTNc9HC)I|!E#*+DHH%^pQ&ho8z0VAg8M=-hEwhjURbn#)BlbYl{Ol45MKrOLRtjS04S01z5Zw#VRnKCp5PTt`$9#kMc8-qDBT?uabgC$Md`mX>=tKZ<4)rw>@#9r3DoShfZ$Fy&QJ0jvS!YlrOISIQJIq(T)llrmf;shp!6?zu{iT7m74XSlmK!1i?~u!atRpis6!eO_lPLZZ5CHIk!Y3$KhqW8ZY7EHi^pF}J-`++qQ;v&qVO;79T^S(td^>E$#zJB;Cw&pGwUN_O3%_nQqR_YboQ<#YQt!AWoFaEwE}eUuCH$11QbjJ+J{Yb5%apei-^6z$n+*5!z6)^da1Widnx;X*b%jN7w5tmOsiLeGyQlO~+C9*=E;DSG)`rJe!P(j<riVy~K?#D|o^d!v!?kU9j@QEHMAT>JHjZPMpv^k84u=3JX_qvL(g(_K;x|GG|7;YupP?t}6EX}t)+OIOR;k50XXec7EG<b9*0ur8z>)eP<5;s`Rt<~DydDv-|7NTsJpxXD;{wMFR?C~VH?LMHMAUJm1d4$;{jPI!7yY0G)*w6Smnor|J->Jn-Jxibv~);V9odMV6GYcOFiI*9OuPP2V_&777)-kZ626$YO}vU|_YLKS=8Ze1-_qjV>nB+9)>7o5bXNij@^8@;d(s7b?I0ueADON4Fn6^CYQ^9eCRGAX98Uj;n72!D**nNqo*LUWPE49rFt51eyO{f%nh>#D*$yA<%SBRPtX(NrZHpfaGpDxzsoT;><8G%pr1!&bC3gt+MlNKS^n<ltbZV&itD7Ey{xdp9``#lo><YPlL&Tg1`s?M@OdA~CLG{+aVE2RdG0*u?~Q1sLU=m^)!>)Z0;SKeTQonjGTp2F4z0i6vrNj}+vf1amsqJc~W*C~jL)8O=tbbf~j&A<6D};)rjS`}r>4^JOwYQYmqfO;Ox({k~{Vk6k@i#I;!Wk7NIszN~lY#4f#Q@uK3dv1EJOqIq~F%r@3a%_g^|mt2|41l<+#Jf};i0<}u;GBYd;m+WrNmpk>kybOkf?jTk2KtyB{ysU?rV9Dz&b~xr}1MpclSDQ5)`B*v9bT#9$><M_fiFU}_%uGeF=aJW|(xJccDdWgCAE%wmuD!MEldgOv@1ypVuRVt<T_`!<<ktsh`5fT!9pxre5oF2vzz^<b`Cu_?1u87ltc9x{rtWmaD~Hf&GH~DpU=ocV&JohZ^>d_%$f>#*OvDuW<YH&7vd@QtQF=m)fkT^-YRICw?@*0p4^Bv_3Mr-C%ITOLx;-+S#pnvuT;T3G4<`dm=K=~uKVDvDU@Q@=`?3gOTUm!w8B0rh$JV~D`3p^vb_4wa5-P+|CD>f?8{fv~uMUebY8{UOfGlp0Y0<MkCy&kjIdAPplDU#dD$QV{<++5s`*t~$l@`**acl}o!o6=_0%JG5#iyK<3ESs$XnzPDoV_gpq&I*SA1uq|X42Q{Q;Zmbq6@ZXvv)l*#rWhv$qGBhT_mzBG!kP++kKp}gd^K1hU@1+%ieWYzzVl7`VaPV&=qyI;{|S2Yv$6mWHOE>(@m~jM@RnQDchVk6G5Cq_bFtvlUbz!HK%o=ti(du>>dfzFz7zD#^9yQpdG*MQuf60!>qJCwz5N<Uk5}O>L^MD2}0?R*jRVK_^Cb)c%;qTQI7WdRTluoq9xA&^sl8^vS16(iWx^=E(l7o1N-6BOdz63WEl2TC%tf4Xg4Osab?y)8mX|hSv4o+Iz3HGqrpD29LpKVMz0k<P;U5UBC(AV^oir$SaDm*@)37R#3sPH+OZuj6UXA1No-sEB|lu$ZNPNZ+H~Dw?2-k%=-lH@BpH``vS|XBbA;GAlc8?dT`zBEhZ7+un?bHn*??=i5AW1#o=OJ}z%1f&H?WyF1VEO<UH!_m7#rIw1X!De2TQ)|N;H;r&)Q3O1n&`ur<_Oviiv(XS7MwwK_WM+aPm@`^;|@uaE#4&<mTXQMCjh0?r+=sUVprXsbze^j@Ieg(zO#v$`Po@wF7vFm#wo@l1;{Hy=kuy4sF_(sxK{YLH{`nWg;DBy6Ot!?x<yN!b~`jL7azWk#7f(-npDsFeRPH1QJ2jSTiL#-*#A~N>$EgPdF4R%i~6_Hx}c=gd*g!PO4iYDtOIVTL3X%rE5R+f`@Woy6-7s6;!}*Jl=311e)w0Kt?#bJMCb7e(A&6*1k&4ds}*hcI6dJ9FNV`r93ATDp2K{RiC%KBGQ@4;Vh)cts}v9ZPK=MnC8}?ca>b^*nxOfh#3HGOP)69@}!a#FykB?Si5^;W2|jAwA|q$R%wPeTRLnX`M7-^McYtcNSBp@&+YD`V*0=pr>jO`kT|0IeQ(Aja;<IAiH^ooDV?~iqg!HXZ#()l9Ntu7)<KkMXQ7R460yn*2Gxm8q_!)^!971b<tuH(J&i3^YreaRs{ud~5VnO9L9ekB)k}HA;M%)U20Y(f9OjL{VCPoqh55!hZXD`GKELvL(`;{BE(>;f4JVs<f0iy!+oeHob8^zh5VYF5y`(*x&!=~>$Oss-%l4dS)ld~ZWw7!z(+t(2sjEScoqJoXI<;khbGj8Q^jLV_KXaqvE(cf>ZLk+6xd^lO^OKyd8A&%P2|Mlc#)d?&zMG;`Wi~G_h<2IYi--aw+1&8p4u`_?LERe3dv<KZ8>c(g$%W@pAPck=M{|zZciS>TC(7iY9NXpWUa(#5HVb%Z)eV!|>`21xle2sY`J3Ztu3;-9ousr`T9xEJPY&#Bq*&{<%CikJn-mZ-Xf4AGzl&#s;rt>%RGNut(Y-;!9^XQ2<TI|sshvo;Z4JB{7$s&9Eenm{qTtDk_;OoA6YM;43dVchVQLxWV|cfMZk?c*u5O&gIIPannUMi8+Q~Z$nP5Axln@x7Zo(eIKePu#661ER3$zKBhF({yTX*H%6;HBgJGvZII$4dM_o*~OhR*{(OC}iGbP*F%j&N@l@n#b^96_-26hba_K3Bpk{RJK@4d#{FD9-zb7k@{MzWUjk?F?{5cWu7QHS5*B55^qX7Si2D*J(UoSN}OCbGfuFEi3TcQ}aqEYY$-M$R4-l2tGB!*ujK3pGxIU*|Q&%c1SZzM(xwZ(3T!qH<ukDl>=&+m3D@uQd6Oz(ewoHM~FTz$+C0R>R~vF33V&n5(vIcQxZ(VyJj9MgNt}U$U-)5o+MchYMr`=^m<sPdgzu_9l(*y@*&q^oC^edSt3pJtoblzZRZh2CYOzN*O@<|aV6k$x8<&De(JY<!$4H>+Co*UJF!blPQ7#@QQ+48O-4LaY;jL<$#?pztVAVvVeP6+slWz2T=G!|k%R}y%@mjm?bRt~jn5E*uX<WEWdmrKl%ha)-7Sv%haKn5qCzz8TrCgOzR-<<*-Uc1T19vL>Uc9JT*KYcZkvW%bE_Db`r1dp!_`l&k{22aQMM>WI?zmvBK1hpnuL9=6mUwj>9ZIsLcVEXf3CX6t8x+|=Hzjo-;-Y3me1z)_C0_#=gV#cDGRZIgOFU(g>e>7>wK{dRg05oIUlrFR;~Di%#G6!xUsE0<I{|6%_i!WRP$^yiYvHAYSU80&XLi!|I}z?(b;5#Nf~S6SSL@+da^onnsB7kiR3ys+Fy+7&?S)V!3%$;apF@!u-B0=GGJGNQMLh1p{?sEqsd6Ha+)7zYwrx-6W&M-UblSnG7LvKS77G#g44Y0%;63=Wo!7u{I=F82eP@<akpn3i=7Y`79u}zbd(U3oD7CTanqOt)Szk%h3E@QG~h&vOE38_wL3<GP^`_b`GiAE57GE3M2}oJ=5Ezypt}Zl?Q|ehOEO7!kB>rC)jXU?q@IeRfx>z2_SQJC8d4TRPfscDE<5;=nF55<ldwCg3%Zt$q0v#C%PhkkY&9CT<w~RLNtC5iumuBSG}~L(wvEdajwNHkV(Wk~l7H>YgiiRPg#jCTqfN>^77IZjr+BC0HUjL+Wtl&_hOwFwbT}qXu)R&#!=p%blx;QR6f$v^jzq#fb>@m0t0cy&WJiGDzR$_E{2ff55`lClvH=~9nG2hz?U>h|>8D-u!aU4UW3nfzaiFIdxr}O3u#twveIPL?ZX4DTi4ooEJe{QbbB6VG?OD&Mi7yKYYMYA>*Kl;6Y6`Vv-QhxW<;-LqEg#FBVItqkCU&z+A-a{tN_X$+pwzJ(Tx`~@HRM~_lf8J|oj(xPq;rbn)^1=VhuE42%`1)YBsLtDgaSY%0vS0_TU3)inZ&l8813>nV+kOYt7iB)5u~6HQ|fgi@q-=hPbZ_@d{J^BBkbHN<PMa7-svt!o+yf0R}M1NfiD$&4sVXsLZ;3j&Tf2oZknnO=PRMRp6v6ffNzR$4yhRnbwU{?iXruidUmM6)=0DIm>2vucebdwd7za=;VO6()9}V`pXa<dEQ0QU)kS$m5xM3T_l0m&0fA09E#_n7F5MJxl$N3Sexq8s)0(owWL9DiC%=3t0Ap!hL~4b`X)_88T?02n6umNt56Y29gU45;BtHeLo5V3R?!gf_Z`%#hh(94LY1OE0^R8&^@zvw5dl<;4ymV?*(~ee<wdI-8xU$R8e0F2?fdRWWWtRu^^yJIgJk2_&MAlGJ7RG)b*Iy@tdpTR)mlZ<pm$;so50wxpQj8Q?Dc-SKD?+t06yhE+G*fC+q@P%|0%vdGQW6Kqj1P?cNba=C?KWj(6Y2I_B1u-NO`?HR%Hj1{aZ~<=|1tn$t2!Q>xE6Ciq(I&9?ifpOIEE#OJ$z*1UL>0dZPWJU(iZnSg~HlOF50|2wT@TKJ=5Hg#M15!k}1E0oDOSmYdP_4>OmrNMw0pdh*_@-DQA#hj*ikS1w?HbYhzj%w0Dx6?Z$9LC6<jeymBI$ozJn}>Ij8ahlbsgb94M=)|f`4HW3L4>wH^vW<=Z;Z8NCSZP96{Myu9z@{VgY_oYyGli@b+W#~YDP4C=wzUBzc$50%pxifK|0GMb9qTyi0QA|qe2D&VRRLQm59D9<t)yUa~sZ(M-vsFd~-hU>no)qbrG%+*>b*)?;hhqDhvOqJj@Nm<dpW7l@qe|IkRCUD?#ASMHj)fW(f0MFxPE^V7DMQWCF|}WS&9ptf&jQwD8%TK0yCz%<jk(sOk{<c#3s{SLGH6!Wc@O<%LIjc0VuzCilII-WP$T9~;ro2OQVbtAyHc~?6i8TEZHkd~Hy7`<tZORgX3w2DwG9qyLE#eMQE-6l>ZdlELb*^SU0F=lXNO{SMHkTp0k)^M<<2!{3i;r99mOGUv0p_7o9?hf4B?bBdGf7WVg?I^DWOkdE|;}C9B~}sK3kD0T|^2%AZ;yA7=LTrNR?yQ36=<SMrFH^MZf5b#^$X#Hmd9bjcxMc2RtobgS8gVdvv(J2nV0-BsmV4uNleLnG<it>h(;dnuM0l_NIC8V8<ZmQe%ylwKK{H>y>YP=JwGO1gD8AU#X2(n2#B(d+luGfVNrH>^(p*gJ6e&byAaRMZYx;_r|kyJeq0R<Gp2MMzUpFahHY*p4h^Dn3k7{y|_l_IUq*%lqjNfb8;)xN#T|8Ztdg?6(vOMD2A#k*b*eR9)>+5S!paZnRa`}m9oRZa$P5)UbKe>6KQNS_BCVyTr5VFXu-dXH8+b~j6{OX9)r(UUUuXyIuMsN(c`ldcMUqFVq*-Y8{5=@q?f&R%(Gs%;}T-a_Npq*$!uE)^zp4zUN+`2rPss&Z_-K}R{=aAEN7h!jvt)l4&kx|Iy1%+o&!O<x|NovTMq8MbtFbWR5}TtTNq7}lS4(Q2UDYnD+pYMtt66YwU&N+&N{0KRAFupdmKJuS2_e^BM;NAPD&p9xIP>>s@J?=`zT&2B(`PIJt49TiHt4{$i1_sl5TdP5asQljWJkYG%0pM$}*GkRi)rOmu)5|;JOq(Skn`SHGxiwmx$Zi=-Vr6tJjvBCvuEj8`Rw$e*!&i`dg?rXlHlUj;pyFciP8M*E2bemdSLil<e$|)kD9=cswUx6YZ87MPZ7LCj?t?P?RzVpj+TlTc)GHvN<@Ex53?LOP<Q33)tCgj@c@4L{~G}?Qm@;^YGl(NW1b0AhMYG@B_+SNSal>W4d^l1Z}5Xp*qNRCV08a&bMTt=2&yVT)<aRoOZkyKT6!CU@H`({k-Ho7RtQuPy;jZ3M+ZMz0+iaLzUc)tc9JuCS6M|oF}j;AoVVpUCquSSnd|9YM32N_laPpQ<k>5OhRE(*@Nr68V_Ksyay-URnLQGcdJt*pBE9X?R6xnjZCbA3C}WE+qj(xcpSo14>*c64|3Y=>rAGxzOUseItBr}Iw?T$`NAJ^M%IHpo^d;)%RIm;t}X$Eph*9?UXY`4jBHt*8Kg|4bFqfI5>=ub-0xf;vQjwbm)BCXOo8*maSSg+H@OcHQ=6x?pI*>apcp3=&*1{`wS=?2w>lEtK+LJc60MDON3}D~oxF>*Kp<2I&6@39sFy*-#$@Uzli(_lJhVNmgddo0CKx&8ipf|b<2lqL9cO$M<=rmFtX9pV0zX9JtqtZ0rX-;{*~CKCL#~RzU1r?!3>`##R^09ClkK3)4_g~XsxvXyG)Bc|oydWA?GnTMAk~J&1-(lRRadL-9k_Cew5G?Nux~V?rJ@w=q66<}zskvrWq_GF7(dSi+MaYDj1H2#E!|8n_7#kRwsU^itC906;%_6tH7G0_>vVMy4^Tj23il@+V4n}sM<-Jp@jL=!lTwkWb|N(4-*#PtNN8?tb=deJ7UiL3)CF2Y?j|uDI|x6U%WZ=G=4l~&k6xk?S~U_K`qEvkYh6z)Kx8lNdXr0#MWMxTV{tGJ(Cb{QOfczVtLFD5qxK*pcmt#q$)io%_}nWMJDA;ykoI{wfw`5MDA6=}DtW~^TPb66t`qO_f&7*jLzzh%OJsyDv^v=2O*S?IPhAFWGmtpRHRa`L&t2?Fl9-IKYMPjP{XiN!E3IA?b~tc%g>6sgtI{b)9VdelM;0c;Bug}pzUZ>U#TI3G1cIrZ&q~l-eYN5W?t>6fpaG#Ii@Oj8o`t@+jsynDaw&E35B)<L&4bSQv=khKGa_S47N)uRv`Sodbx8GI;Y`(@&yQVX_pmHg9BjW;U_|L4w*a?<_I8Jh`%sY@?O_2;rpQ5@ATrfcfShH!K@7>VbI<Wu%;q@Eo-SDN5z%rsk4#6IFJ%U3P{*CEKSGA>IeKXBT$x%8N;gy4rd&Egqfv!IGce~KZiLY~(5Pi|XD}IO5NDztL5r(KI_a5am}Cp2;!d>WgGdF~Ww~rdI%2LMU#t%HDGV+E;Ig&b<*k=+`c$|?*}<8v)jdNW;Kc%q9V%R~C^<=cP}ej>hC9xcGv?;WTq?%rv$oWv<}L2_R5F@l++JJ2-Xxv7m2Iq^j@RT6n})phSg9!#Qt6~}DMh!bW)#>-?tTg5@knj}Gbgea@Y+y6K}{-Z6zu|Y>2`}dUrKpv0t%Em%FH%iRl*6s2z0%D5lw`f3-{c|*+Y@RcDR{r=z3vFURv9OXHeN@=p@>~3M{|J&s#QEZ<Ym;4tX}gGaT|MV{)&omrkVa7JP{l9Bts?3PRV%9XcB%mzeFmFWD+Fr)_kZ?{lN@Aks=o<)UXf-nQc-+ah&b(lH@zuU?q(mZc&v-<*{CR=Aog#oD_<pdy{H6NU2yqy#Ckkn9ig<hXdm(oW1?fa&aDR+%b^JzG>-KJR{-EOrX3R4fxvb_B7C`ie*Q$_0BSU6)^6*hWQao>?Q&(Rvyju22Hc`)W+G5s~G(J-*%IWva`K!jbw4+tGP;HHN3r*uHm)V#Bn51tH3)<>{a59pW(DE&7eVU*Q>hn(EBq!mLgg8+*8DC+WT&9(GrlQnKRv6Oj-KzN5p9IYlr~4)?&C-Og?gz1}`sYq7IldbJCZ*ea0(cGJ0&n&)iZdQhZ63BF8%d7<EE`jK%k>F4Qo3L3VT7y|b^9OUMr>BgwIjjg(K2AL9rd44{qgjVtWQ6~L~vg1^T(~hacVBJK;VH^4`K+a0cT&`q3IXPyj15saPr-NLSmEm4wR|vz&I#zXu%2>x55!Ov#Cm;1^CP%lcHEflw5<Bx%TuP`n%Z|(asVw#VQoYm3jUp_ECnoFZI)5BU!Qqgu9F}oMCvPv|vOOCq(XLfA6G*y6d-+ravWWpUcH1(o@F=YA6k9%#3QV9&kyLl=uCt5FmB^ZoI)@#5B1y4Hx|+$CW?R74JfZRCHfAm6E~3+a+BPSN;+h*r7o$n1=969Vf}C6n<Fy*nWO*XlP1kFEo^Rue%{gKpM4-GUCBeN>q7_ROoGG#$u=_nWTsR5|#TPzQ+x10%&<<`<&{3Q<MoX?Zvn@6P5ZzYRfpJL)c`q9@H<lV!>&V{P&evV$ghqDh>?GHk`UB(w%QZtpU?62Hv=~ocy!I|Oz+**zeh$WcsdQ_UNDQYoc}ks@PH`8^ZZhqfx38RI>=KOmX5+ZButhTCeWPHfGSU6SIcRy3%q)dq%yP&~0*yhfG|AORxkWk`nDiF589A&TUA;I4oQp!bKAMYme`#HToo&TcOSkt97lu-4xZA6^R!Yc;PphuNzUiS)vw3@#m9UK*-Fln#J~|Z(6~B+E1;&GoYq)8&o3r6W0CG)7-BX#TozW_PT3$RQbXgpVna08;2D_c6u!bSeMLouafdnxm)3pf+2;>IJEGhtpQ`O9%?242CaXFe5SM76Jaz@#e*X{Mr_{AA%26+M<C(76*%xsV4$~J3FSm!RdpFBk?PP<s`41#?sW~U%uxNaT$3u<t+_HV~E=cd^L_;6LJ5^hj%HO_Ea3FjLP#~JcMXqi|JFZQx9z!02uEd}|q;GL(~xHQ^bd^;i-m!m{sBo%ut^`O}bF1G%SQaaSe1Crg9DBhJW%!AFD_ZX{tWj};-q%}ug0_~X%i9~Q|S|PSX+25=<A-Wmukqfps7Co`UcC|z}j#~R1b>&1Pfkd>W#(~b$0z=0Omm308{UGc;PCT7ff!wZ>naY+O9@+@+ZV16<w#T+?y-B20LwP6}8lvS~1@COQ%wastm#a|!fOnjyhP0IIq0SD<Eajq9V0Ts3O$ESM1z%i7`$4LX<k-{YM5`OveAAFZ_DvwO?=sa|yE251v(N}irmJl~GKaZCEQ?)ABfEV7QXI~UzTM6bp#_@qRtKII?>dv~70%$c^06Wbi$O+kLFv?aTpOe&wpKeT_*Ye1<Fd{cshl$zv)ASM$}x-{;l@tY<sDUK1bADoqG%=IryV6Q8_OdT*EwJ2$W2+yHdi#KMvV13ZeQA((`hn2jBcP{%yYmbSFwEA%wthFDy2L1O~F5RdRl?l#C9CVy~9~@-`GIaL(NfkcNQBZ>xk1Uj4Gvy6Sp%Z5yS8VT9$^cy45Xrkot(EHx4wGnu~FdGAEgOJk{;h(aNla*2z32PKyvc+jw)^kYDaMgJHVsb^u^35V+9I>S&4ci(!3L%Qa5Nc`7UHLzDPXUgMKNI_zz9fQm~(auZ;#9vz)onyT9;7c$ivR{I@~JZ_EUN)O8P1Slw1>9%4WXJi>j1+zth#_+7eL5getAa*XdM3$I>qaw>TPax}Dx}jwPD;7Z@BeXX7o~n_9qGzAD;9@McK_j*Jl<G2|y!EgVpcr4$_&jSp=jY|-v?y~+ui|WblZ8B(@+8<PHtDC~dO58gXe-e%<ythSKsz(4$+g9*;y5c{Gq$aJxnOIL(8YMx87Kh=nHsV!N$SKM)j|d6<kMxGY6fs{H*0mM%&DB1V69<S^rB>|W1aLyd~#p+*yo($KDy}mXl}PQ#cKD&7Vxvw-1>K$#cGo|+1!3xic4h9TOSn)2N878C29e_J6_D`LSk*72sRR+q)wLa(;<8_OGS!qxt-0EzMwVeC}m4g&{N7o&}=;1WFo44rbfG7qtLsYab%I**|xJWHf_fTfN}u`vMue0mn6xl?kwHQb!Tgv^{|q9b(Z&f>(stV2E8pNS`M@67K5|Qrg>OO=~RuYZ|IA?BJ7gU9<HPbC_p%TaYx0<ySHIp#!<1gBAECZzchBN6{GAax?I^)pznArq-}T<1Q$u%#&(o#DX*Sk+Mpvp%Gh^++>-nW=VEw33g>k#5nMv4PO2A`&OsSxn8T_TIbeG)x5zgp)VP?+%#)c@(wV|f-F@6kyR0gf5WFcY3$|s3V_nB+f0P<V#CF<^BwOcH!{-9dE?c)qHDFJ&TsXO6Jkb~gsy4oto(z$WhrTeyOJ@`=$$Z1zV-{t5;kb^q{D6N|nlEwjI31<2=yG&C92#|BwJ4WSw3u+N(=GQNjpD&&%qhiURBr3qFQNs4vO4hcATQ4<$@8gQ-gX1RBHQ(^SHpo<a40eBp*N8VVJAR%y1R88SeFJ~(TgcT+bkXDl>BPNls#$2kJ}5Sq34_xBlRTj!m@b*M+en-xRm$S^ZjjC1Y_)JJ~}MeM4Z}zuoIp1YDALtHozv^PNX0#F@jr)omzNN-XTEwLcYYUh0U@Nf*jScFP6caWN2-bhhAtzS^)=;m@y3>Tq`QT65d&<DU)3%dd=>v5v%M7N6flJK;IBd9gBrn)a&RhtMp!RI-=9qJbh@235CekC66nbS}ko8IuePL)%fEwDJ^}-DH_NvOQHC_Y`+{D&PczXBbP!QnAt)&y-y-Je1YuT)dA+D<yp2iO7+&QO5?C4nyYFDPqOsIx~xRJJvla>mzV)?$yG$WIl!t^IzsU57Vx7Na_uHh=%_J(PyQiU?+)CtXwDX?BFS1NxFB*9X9BVg<T;V$aseCdwUuM^6xrlwCr4QrHNosK=1z^WSZvjZ^eDJ_pt?mcF{mtD`>mtcpn>o<na*)Vj<Shs^Z-HpY(y`+d)K;0R1cRiI}a>ky%3e6qDV+$dN?F{gqrgZpRCZR-JZd72WZv{FiQadT-Jy)DdBZt3-Q72tX`T$x=qJu-<Xv;SeHF+s75&tlqK7!S+Q9OqDr;OFf>gjD8x06yTK8Vo-bnma=E^n#f@)@Jn;tKT&{0arbgu(cv&lt1pZaVOC<5Hcgw%Z`BG8)zuu@}?Id2Sb+vD8k}Unp7*lUx4O|^_{AN-Az`rcVH;$HMN|Kq?+g}zh^lo_@E6nHb>c`{x{H_mz{_ddjH>!=}>5sX!Y0vLEqVu)0hF3~hSB1eV+M0sjsCtg9P?Z{~o<<w>8_91;tccgTDsJEn&t~7$soFUlYrMG(>fS2(UJug;>o6KeG@u4q#v0@^c(T?cQaP$#Asf#))ej$>ybbAMH9{qntl|0yjk|B}*Uo$jr&2W>D}Ru1heAboCFm2?c!Nq|83SVqtJPF;ZaC{@l5FJi_%BgjfiqaGjMwT^8LJg>V@<ckToK>1<8guKZ{NO+nTbVp3o@{wIfZ$*ESUYfMQx-NPK_G{o^k!9PsL6wti<w?O!Fh=3Or^<ve~cwiHxj>yhZQ)uHn2#=F-8`R+$l10jnQqSr)ID-qi0Zf%=5k`9?Iy(L;^_j6u&68SO7-`RKo&;}OnWx>lG>(Ic4^c)<A2oX7a0QmR3yHp#5C4<?L75LI=4nCy6??rlPgOGZ?s!LgETj?npW?Qv=2f4o(&dj0LEDNB9ijONFZI`D@+QV_=~ukJzhl53-x<t-1WjiCnSpRS*GNSAuW_9NC`VKU)Ap}HxH#Ly~|p=9#OTt1|02rmP=GO69FOjjJeS6BOP0d-vJztN})$Z!&40k7yZmKg9FViT#>D5<>H3BJRqx2p(MvP|mkY0!IrXlQ<F)My_p5evugfZpRWW<K6lLUZhtr*y`d40yMEEbOKLuXIF*V0J5JBr{`;P<0ZW&b#$|aLV<573~x0dh>OqU(54q6WTm_k4s(Ib^Z^-(7V1fJDK6fz>lli=(46XIg2zuWq=#q-aC9Qa}tAwALjf&Rnq=U8Fly{e_e6^{CO`K1L>9TGRrZP${LMT@0OJyv3GVSi~EoD?A|SVl>$w#u3$ev)nXo7Ad~dF2@PQw6TE5jJ+l7C{^yU~Pg95^W+hvIJU?c3xF`zZyQQ&TG3LjX<~#Jy&;IAFM5c;(`t7zZksdLcq6p$uU9?^D-J&<$)~5n#T4g?Y__1VpU`g))ZAluqOS6}EL!(R>mntd9_0#Y=S5?rFY8G|#H=pU#<)+W~3-9xwg?GSD`ugoNW<%mS89zS=irnj{Zg3w{nS9zZ%$O3H70urGq#MlD26ZlcHo~urRR_~eJ$h$x#%4n=bxwZ-B!+Xia!{K`V<4z4Q2!Fq6-yguFySNec~>JH*PRNOxF3TfL)vc|c^fk#x(#@uLfZsYBsWTb+@aDswGTIEs4e4@r_}qdHlPXb$Gy&9W&Lh(e>hRI@7Wa@EKzt?HU*;Nd$Du9-)&na=3i_=HxX_abG6?kMmD!#;L4|WeJeGVst(lE=v`AqUNXhc@*n<j!+d9DW+?&p(qJ{?wP=!jWf+DUYLYb!(c-Z{A44bR=$PTf@0oBn!^cX#uY?s~68RCYT>nM_FSESD+#2aAV+vC>VvUBoh5dL_<0(;oyYpWf{n`k1qkNqFo~|D{#Xqmx#sfxm3f1{D<9nnGr=s;)B2gW8MB9Wtmgi9XPbU1z$!Q+y>gev~m6$(c;Z6GbMDLcHbJtzHz95&T1`MyL5~XDZIIyc5kZKYSV!M-@sSF>waFe%g_@-uP-@T7YVGLyXtNyBActO4og0F<V>r!ytAk5~!eytZqxTHg>Tbemijo*{ad?`(-Hr8mWXAad`RrwI=+2J?nv^`E2&+EPQe%epV&_<Y{ytV}Gt6|Iwl`pC-TUF+1s`B<53JgA7_XEu}8p?fhi#N?Q1LK=uKb+)io%`{Y&S&3#etU>dOnGYk52HYRFM4og54+G8LCymX=&y&}?(4nh8pDdJ+t!rQ@XjCG*Xw;rht-;|XY@bYmh@r2+n27mUv5lap4&fmsYjA@&!r;#Ap6T*N+lfBT+1g)Z&MnCs!P$neWLfr2iVW|yC!`GjZ!n}G38;9bPc+MEl-V^r79eX7q*57v>oC>5C(uHYMxWnZe6c4c&(8y<$HMT&7$?|+;&)e$enipALQb&AlgXqDcCY*FhV?)Bu%^@=N7HS*yrwIIL+NjGhubx-t++)s5(O7IbpO=<0K8@akKuIdL;^DWh85x^<xG_=e;&k^`x!`<JXt2PIw*qXw)W~JW+MGFi#s-!281+^zC`!S5r{5hrrZYp;h-F@67;MoAr9M(*dqq;&mrB-IA_BCPd^h1b$*T_@ENX61V|q(KKkB5%lB958ux_COjT|Z(+DG>(7@*;ClvYM43luHDZ8uwJ~N<J&zW2)bUd3?XDTpn>7yTXl_np#f}!rN{xdhM%*wrzjDVavrCI>zCBU???-2UJ?O>9hM-TODvmZ@jl+}`$Eb#@E$DIWzUQ@9@~L98@_O};n)Yza`;e@$U{(KK%J3Ec?-cSDc9=)H-yP##O#7hOX8ToO%uZzp%THBr&T+5h_3!E8FOo3-6%EvmV0+->)TMgW2d8OfbbjH@t<g{J{PDc6yA(y=jwD$G3|8H<<mx6|Ml!*0+t)^oCt6tYi2%cox~`{y^B*Q_42Eja#Lt^CiS+gw;l1Yj$HELLnE|&t?%$S(wm6kFTATX+k8Ar+OYDAgF?hOG7|F;p{aT$2Xw6+4%+OK`x6$v9^SHj4!yElT@whiUQ28a8%8n0Yk?7~eybK+03|5z8iGGZ~vm#9@-|5v#OKcgeehB1DvHjFpq<#GH7X<$N_D>^>$9&a9R0*a;g})E}zAzYV7rWip{K_s?BD*oez`Km8(fAZ9NHbmfI;07sLTjy0pi5z+!yf<CFs_EDY2*va)fj%N+s&`G_IqP62Sm&O_O}7rv%){=ha{`9(4+QKMuelOwSnuJW4=!XUboL*?zP%c_!qAIhVJH;47)Ox`F^FzAkllB^fBnV4SlwUr?r0gsehKO|2TY`Yf@41%uWW(4DJIabFzPLQ*nLHgQ)0kle3a;5*ol?pEhX&!Z7(e$=-FiG~ryC_n6Jl=ryR<&J@rmu0HyU9|rO7pZ1rZze-fRJl_7s)7;GOhc=N8p?%ZkbW_q#3sRS&1O4Je^f^|31bVy8^Q8l$rwo68W%Cew8K+IlH4A-jUWQLH_xqcDy-H1g;*w@^UnO}T{Ln4>)+W({R^1~!9cEu0uwP91bv*L|_z#@=XYc*%9JCpA;`)DT*9VKA6S#L*L!T!(KB(cxUE(#ee}C-1-55S!_WUmA`w7#>HQ`;4c2{Oo4gEj%r($bC0nNNLKS}GUHF`|1j2zpB5jlGQAD+?tsi`F`&n&cLp*B!}(!PBAMyaHjcju~n8lr0MdQ$_hmGcBvQX4b0>KcsJ99hfvNJ4EyjD}jig_Wp!Du<_=CB4`I@`Ha_0Kh21c(;UH@2XBie)PT(Le19TLu){9^+5)#S=-?^8e#ap5jGl;hpC{T(Te&EP_sw`0?lUhq1nWX1|ESSquE@<Ct$ztRck2lOd1UOo)-Z_&<jWyeAW1w2NvM5$OX~75RCfo8DOj*MuYcbArqq?dd7GgrvtpAIDo#GAn>qY$Y-<$!55&x&ny1C4xc`E&{)T(9s@(@1$#oFXLw^q1O&hCf}XqlW*7S01tDgi|DFP$*$N>Ky5}=ngI_HKfkLka_<Z-RCT<`6B^Dq0%nrmCctCBozEUg%eh^5&Z1laD&tw|ne^v_weZXQuqVTH)q7MWc?f~(>T1DU$y@3}pyP^*Ge$n?rLm-p-Aov^O^67g#5`<syDu}#l^uKTnNHF-SHT39Ot^|jCFM;7#z6=SWFM(fD@#vlm|AvB}d?czf;U**<1b%@H1(C;r$TRn#pfUc1;i3@ysu6iXAryMnJJk0|;-K00fZ8-()HIDxzSHP>VXLr-?3LD|k6Le<8H&C#9&-v5ezp_zl|`WFD{lGWXP1gTZklFe0Q_>9fmg20oFMQDSMbF~fCgWY5`0uGlXt-vrsp&JLJtfvDGVXM7!dec;-SZl&QzRG=*8~jf9c?_eXo3lVcGsy3hRfyW~m<vK8xJ%gPxb|_dRR~2A}<pagMoCKa9Kr4ZZ?Jpf4StA3=Z7_aIBuYz#g-J3snD*G%U7QRo+a55dZnUjJv-Snfe|2;_N-^gr$(S4sN)&!*+~hh9XP{;w^@9|%0_x<BZ9)%ao`^9TJe8bja<wRm*Rffuecpm8AZDsb@`OAb5+nq~|f0O41ykCC<BdN$(tN=+-|&6G&8rri)4jd@V}461+TF`@ENmTc76s_1;E9&~A^<h7_3u!7%%+BZ&^>R&WNHinqhxat^K8-qSV-6IIx#+Y@x>KH$$IR$+T%QLiIQ~4cv80NnXyDRclhe8^52>dj~JtpXGtiH7wD+9F+;RTuMXZUV}Rzt1A>)^2O1%=PN&`X##(zInkKHuXqz9LO8z1AoL^#!3{Q1&s+-Q}(}8Tcg+AHM5#(YnOb>iG_@eMtSro41iDtn^xJz2!CEZ$K}K%C8J~qj`2ob9%Kl*?#-H(!1_@4#z7-&9;7i6-0K*@-+96#(2nS7z-$2^@d*AqvyDdwv<XSPNhg9lTYJB3fC_e%{;e;Senr*2H@!>^KKM!-=((olDFuMU#|<lpP*H_yoR*6zZ{{JjXY&vuIKjeTE9`$?Rut7m_p#M2I~L-^c}Q#EO$6w!97CVF=-{TTK$in(qs7z!^?uWHyNe<NcFo#o{54oovjr4-7;i2VM|S}AJi6lC~O$5#rU9S*9{+IWDY-W-%Q+=h{beDca=>`EpKPyRC%dQZ26yiDc&ajpyngpWQZVY4D;yN+%E@Ty`lGRso$QHrUp6J1-&BYw(8%K<9#OQHu!@l-YaPj64a8IpS`+~(^Mzr$EM!69^^@n=k$oVD=B`JD7{t||GpSmuT%p7#N5$Q^M6E-EcEZF>mg_O`lkBb@==rgT>fArrtXzekYsAYGMrX3!i-;3w7<Q*)!C)OX-QRq=k~_6l3qPHVMOWOvYoM`nRbOCa2rNdt%)Eq*E<3|>o4iQ@cvJ)uk=gc#p4a|#>^_~Y0HJ`b8ff3zq#!CbOC%-3zpGKS9J`cur*<g+g@S&SZecu{BHD%y4c_6Z+};YtKwAG3;z6D<+ujN|8s@7s&qL<Pu|}x*Jak(+*a^VReJ-wUZq?gz1)>*UPnHbXTHLBy+bz^cCGKb6=X&}E}=e`j{l;3@pZL|S&Mmlw4h(h{>s$9uG8c<`U`{`D@?lYN&2z|=2OAU<5c>kt9G{|0@o|G$4mM98^?d69Ol!-<@M{kZk7+1Q;*YY-M5>pCs@_}KHbcj{JITNKmYRb>vo&>z`%4(d-(Q%^rJY$EZHy%NH;HP!Eb(25SAaDQ^P-%Vy!esUx~g8XyaT@<36$Lj`P~w*E=u``}5e}u*~zCWuMsw{(?D`5|+aM6Ut??V7$c$FfBS#i)O;Iq}`K@X4=)QI#wC!rFdh3F|KiCK~XmddBzxvd#vdC!wO_QSkULCK4#DgR<#iLFU#9q>9Y~_KDK2^vaY?HRKZm>Ie)G_xmGef&7g7Yi>ha>>#6KnW%g$rrhqi?YiNG0+t!BvVWG=^+p6!7KH1+@dw*vXf6Ebge(wl=OVgb<d5Gq;+3tg!vASh5A~jM&xvPd5O{N3Tg!gWq2FxC_Bv)4T{JxO#DH{0lvDjY^<$AiBUk92I#skoAtL*<!PgES*YILi=YTKixnytF7YD<1bY%Kd$*ZAO8Zpih6>X$}fzCZZXuaEijiA`zht@q*-Rx5#5H&#j-(H!$p8uZVeftrS6KK6`Qe3olzlWC=Q$NJ}T;_u)uO7>L~)1BK(9W>vZzTe|FRNok^`b$<1<h~jXX;%146k1)CfhF>)`20$|R!yQ&`Vt8G4t_o;spH;t_u<n%m^1v3Wx@&S;x$a44oWL!$gv|zVy8T<c|@IlQ&^fJXp02yUY_ed+RSd;eD^JJ^8UivKPF5b-|}mZP(B{he={sc<)Sw0QP)EYsN1M+|Ej!olFtACn7n=lV)n*EppWFwHIrl*<uk79+4*LkDvsyaL?zGwRIwXud&cy^(jPkP&u8Cp{Tqr5z4-4Pey*qO+uXMo)?W_%s9Moa0e~ckvU(1_A9Q<Fp>8%~_1r5zV)zP$@#PlE=yJM0_Iw<6o-ml))HLzuvu>K;4>qQ(#_9oz8gZ&;e0oqc<%FT?SRd1Srq}qK+WW<OqUa|KADZxWlJM4hpH{qo{-dM5zGFl5dq92H(3*@lf@&;-1YbO~dCG45N4)<_q_5pO$4um_e}3uXOc!s)ChT<fJMf!JH-?N^!zt(~G6~S;(;|AWflEsxsbLgsahtuo0ink1<{Nzj47wJ3-_WV%sfBOaC|U&_8oEipTZWnxv^SDEB3Rv73>5Gch0ZRu%lA{O;x{^dcLneFQ~0hUZjF(L_o-hgjkdD{ztB#tobj4R{Dc|#1I$K1`MTTtf%!f|`44fy57sF%8%A~8lxm!Mu`nZk&I5lGm_9!X`8s>7vO{}<Xvk0d^zm~ICVd}oC0-IFX_-Bhg^Zv`&m?Jk`Mc#BZhhnfNkvo<3tFwdiO8~@F}!6c$TN$?j@2DqTcv))(N2Au^D+~H5+}&Fbl`RHeT4nIiceIy9$p~n;1QkD&+i`$+@9#KvhPn>tGzY=fIgu%-}Gtb_Rx1F>e~PK4oD~9@tQ<XxG_bKH%1cbv8Me)Snp;z{PjJk7Uo_($CttH&7tbh5&eSei~R57f}<a`yLbN5EbP3?o!(_U_eT5Ok?fjO*NgY>6YRG)l)o+MH`13^jv5vQ-6!GAHv(>BiP!U{it5Unzh!3MjC@8zdv>W6mMU5xN>8*O8j@$MWYPHbFX^hc`ax#Kh(>msU9Lo7qrz+Ity_YLjo#3#{_{f?b;Hm)C+tqO5=j$@U|7RM;5cEcrAo9JjBJROTo<W(k=)L{ANLjp>kPWLG%J5z^$T16g!f*<ZuVqSj;Vnlzqc^sDWjF&Yp-coQA_j->Y@a8Y#Gfo1yUEG3qz-0OYz>Tye0~Dx7LaCT;+F5IsDK6SP<9WejTH^8<SKoy`@F9S2ty^Dg$+>(WVlx;^+~x)HFx)A}z?T%1)oet4?zBIM=r}A0@o6Fa4fxN`F)E{i`7C;W5tdE?xfFa~ySD57ox8`;GS6`Ls<%KL1?Azr_NbQcex<$C?5k_1Bxfd?fSw5z$9-P8BK7-}B+RN0@JYZ@a|xp@VTMeRyc_etiY;z#c7%_;e(?i?vMj-j6u-BRjm69?AKKZ-f7Ob<n!Y-$m50?uu0l`K-6MG`Cjh_VW)f-e3Lp(0E<V-QzsN>1d5Q$=43!hlO4w9nHL;>x-QG{e#RGh41<t28;CP=6_jU(|4Z?ywP?|1HQj{7Wy~n(h-`M0WU>zp9eD4@imjp&KtQuuKINMa_DK`^8=!n=rmEQQOQ%jRQH3@^)mH$d$$4objzymCX5!y>zaM5SAoBy@1Lqu^mNa)48{0j7M;M~eIM9HGr^?m$Ioxi{0BZbV@5f5%zZ74Uq7PLUmHK=m#+z8(<43JSh+qYVSe$}?n@I=8LIk7ohl>sWpMa&P;@QN(2r{dRql`Z+*jt`)o?sbpoOHL{g)OHn2gjAexB;_deV@{^*R=~BL4ig?eYELRgTwNqhGuqeDRo$`i$JPVH2zC=?8x9pUM6C8$6q(#4Z>;u+l>^HI~zMUn3u-UGa|9$biwePyM7#bKG8~V`0W_dVq9?%naAG!waq2y;oR$S0f|+iI^T+a9VsMTDDpouPWY15JhGrt0=F}MpdMD=sv<Xjfqp%08o`!tIkj-x<$L%71~M-E*Vj4o^pyBJ+i8<Prv`-G4Ox!4esB6TKk0szI<5wzxi<X;U51V9>D(Z+3o*5yZzsIcB|{?OgkLtk8dqe;}PzC3PE*OOD!t@9E(5wn!v-0#A^!I8hw6-`>UTD_`@Gk{DV@bzf<`2U%481EcN<3<y`;8Upf3o1yP?$pB~Dx^dAP%s@R@OkFG^+8pt0NHGTQBYFeeu&p-TGwZHSjX@Bd8Y_pVAH?`M%mbRtpm5Ep5P&Ii=i{tN>y0(!s8%EuL&0nNafoa*YW!3f}V<sp~eERf80!W|OBwGrbB^_!cq*b-39&M-#N1c$_jW}g|t!a7nV==e=*@(~n`u6LBj^FO0_uJdkPhk8VPx=Qg@=tyh;KM^a`mT>#lK<lG2E2M<|2r@FM{n<6tz1%uOIDK9hL07#Yg^BRo!<ZE`P<uDlV{h8miyCm@%n@0x;hl;>6BysC0Qgv5l4)7q8C>Rw7N-uH-4$GF}pTsVJM^hPMZ;^O0pUnY&q@Rs>VE8?)`>Y3l3E6RzK<YgDdT~f{hACGefEkRfBGc7Fo?qv@E2;kIblesiGPT^fe6z-!1w}`>jZ?RDIWCQtvH1FfOgWnZHlUe@=?3kt?GvSwAs+#1uEo+8uS+NUcuPux)0thrj-sEyGJ{kSb}{&Fq*qUExN!M(Wq!eN-)-@v6a@qQ~PaL8WN_{mS?Uwf#`T{|8OavLO'
SUBMISSION_SHA256 = '9effac3f92ebd243b3968aac2b492d05b8e4ded130c8d0cee9c0b2d210367006'

main_bytes = zlib.decompress(base64.b85decode(SUBMISSION_B85.encode("ascii")))
assert hashlib.sha256(main_bytes).hexdigest() == SUBMISSION_SHA256
(TEMP / "main.py").write_bytes(main_bytes)

archive = WORK / "submission.tar.gz"
with tarfile.open(archive, "w:gz") as tf:
    info = tarfile.TarInfo("main.py")
    info.size = len(main_bytes)
    info.mode = 0o644
    tf.addfile(info, io.BytesIO(main_bytes))

with tarfile.open(archive, "r:gz") as tf:
    assert tf.getnames() == ["main.py"]
    assert hashlib.sha256(tf.extractfile("main.py").read()).hexdigest() == SUBMISSION_SHA256

print(f"staged {TEMP / 'main.py'}  ({len(main_bytes):,} bytes, sha256={SUBMISSION_SHA256})")
print(f"wrote {archive}  ({archive.stat().st_size:,} bytes)")

# Validator-style smoke: pass the file path so kaggle-environments exercises its
# source loader and last-callable selection, exactly where V17 version 16 failed.
_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 8000}, debug=True)
_env.run([str(TEMP / "main.py"), "starter"])
_final = _env.steps[-1][0]
print(f"validator-style packaged v17_boatlee_adaptive: status={_final.status}  bank={_final.reward:,.0f}")
assert _final.status == "DONE", "packaged v17_boatlee_adaptive did not survive a full season"


%%writefile /tmp/my_agent.py
"""My Kaggriculture agent.

Contract: `agent(obs) -> {"farmer": [op, *args], "hands": [...], "market": [...]}`
Handy reminders:
  - tiles are indexed tiles[y][x]; the farmer is at [x, y]
  - the only shed-access tile while just NW is unlocked is (4, 4)
  - plants die after 2 unwatered days; animals die after 2 unfed days (permanently)
  - end of day dumps every inventory into the shed, which caps at 100 items
"""

def agent(obs):
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]

    market = []
    if priv["seeds"].get("WHEAT", 0) < 4 and me["money"] >= 40:
        market.append(["BUY_SEED", "WHEAT", 4])
    if obs["hour"] == 0:
        market += [["HIRE"]] * 4          # four hands cost 7 coins for the whole day
    wheat = priv["shed"].get("WHEAT", 0)
    if wheat:
        market.append(["SELL", "WHEAT", wheat])

    # One naive farmer loop; the hands just mirror it.
    if tile is None and priv["seeds"].get("WHEAT", 0) > 0:
        op = ["PLANT", "WHEAT"]
    elif isinstance(tile, dict) and tile.get("kind") == "PLANT":
        age = obs["day"] - tile["planted_day"]
        if age >= 4:                       # wait for the full watering bonus window
            op = ["HARVEST"]
        elif not tile["watered_today"]:
            op = ["WATER"]
        else:
            op = ["EAST" if fx < 4 else "WEST"]
    else:
        op = ["EAST" if fx < 4 else "WEST"]

    return {"farmer": op, "hands": [["PASS"]] * len(me["hands"]), "market": market}


# ---------------------------------------------------------------------------
# Choose how to load your challenger: "cell", "dataset" or "archive".
#
# Default is "archive" pointing at the submission.tar.gz built above, so the
# ranking below measures the exact artifact this notebook writes. Switch to
# "cell" to rank the template agent instead, or "dataset" for your own file.
# ---------------------------------------------------------------------------
CHALLENGER_MODE = "archive"

CHALLENGER_NAME = "v17_boatlee_adaptive"   # label used in the results table
DATASET_AGENT_PATH = "/kaggle/input/my-agent-dataset/main.py"
ARCHIVE_PATH = str(WORK / "submission.tar.gz")   # what we just packaged


def _unsafe(name):
    """Reject absolute paths and anything escaping the extraction directory."""
    parts = Path(name).parts
    return Path(name).is_absolute() or ".." in parts or name.startswith("/")


def load_from_archive(archive_path, workdir=None):
    """Extract a submission archive and import the main.py inside it.

    Supports the .tar.gz the competition expects, its siblings (.tgz, .tar.bz2,
    .tar.xz, plain .tar) and .zip. 7-Zip is deliberately not supported: py7zr is
    not installed on Kaggle images.
    """
    archive_path = Path(archive_path)
    if not archive_path.exists():
        raise FileNotFoundError(f"no archive at {archive_path}")
    # Derive from WORK rather than hard-coding /kaggle/working, so this also runs
    # locally or in a fork with a different working directory.
    workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="rank-agent-unpacked-"))
    if workdir.exists():
        shutil.rmtree(workdir)               # never mix two runs' extractions
    workdir.mkdir(parents=True, exist_ok=True)

    # Check zip first: a .zip is not a tarfile, and vice versa.
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as zf:
            bad = [n for n in zf.namelist() if _unsafe(n)]
            if bad:
                raise ValueError(f"unsafe path in archive: {bad[0]}")
            zf.extractall(workdir)
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as tf:
            bad = [n for n in tf.getnames() if _unsafe(n)]
            if bad:
                raise ValueError(f"unsafe path in archive: {bad[0]}")
            try:
                tf.extractall(workdir, filter="data")   # Python 3.12+
            except TypeError:
                tf.extractall(workdir)
    else:
        raise ValueError(
            f"{archive_path.name} is not a readable tar or zip archive. "
            "7-Zip (.7z) is not supported here -- py7zr is not installed on Kaggle "
            "images, and the competition expects submission.tar.gz. Repack with: "
            "tar -czf submission.tar.gz main.py ..."
        )

    main = workdir / "main.py"
    if not main.exists():
        found = sorted(workdir.rglob("main.py"))
        if not found:
            raise FileNotFoundError(
                "no main.py in the archive. The competition requires main.py at the "
                f"root; archive contains: {sorted(p.name for p in workdir.rglob('*'))[:12]}"
            )
        # Not fatal here, but it *is* fatal on submission -- so say so loudly.
        main = found[0]
        print(f"WARNING: main.py is not at the archive root (found at "
              f"{main.relative_to(workdir)}). Kaggle will reject this submission.")
    sys.path.insert(0, str(main.parent))       # so sibling modules import cleanly
    return load_agent(main, "challenger")


if CHALLENGER_MODE == "cell":
    challenger = load_agent("/tmp/my_agent.py", "challenger")
elif CHALLENGER_MODE == "dataset":
    challenger = load_agent(DATASET_AGENT_PATH, "challenger")
elif CHALLENGER_MODE == "archive":
    challenger = load_from_archive(ARCHIVE_PATH)
else:
    raise ValueError(f"unknown CHALLENGER_MODE: {CHALLENGER_MODE!r}")

print("challenger loaded:", CHALLENGER_NAME, "via", CHALLENGER_MODE)


def play(agent_a, agent_b, seed=0, steps=720, debug=False):
    """One episode. Returns (rewards, statuses)."""
    env = make("kaggriculture",
               configuration={"episodeSteps": steps, "seed": seed},
               debug=debug)
    env.run([agent_a, agent_b])
    final = env.steps[-1]
    return [s.reward for s in final], [s.status for s in final]


rewards, statuses = play(challenger, reference["fallow_finn"], seed=1, steps=120, debug=True)
print("120-turn smoke test — rewards:", rewards, "statuses:", statuses)
assert statuses[0] == "DONE", f"challenger did not survive: {statuses[0]}"
print("OK")


# ---- evaluation budget ----------------------------------------------------
SEEDS = [9001, 9002, 9003]     # add more for tighter error bars
FULL_ROUND_ROBIN = False       # True also replays reference-vs-reference (much slower)
# ---------------------------------------------------------------------------

def duel(name_a, agent_a, name_b, agent_b, seeds=SEEDS):
    """Seat-swapped series. Returns a result row from name_a's perspective."""
    wins_a = wins_b = ties = errors = 0
    margins = []
    for seed in seeds:
        for seat_a in (0, 1):
            pair = [agent_a, agent_b] if seat_a == 0 else [agent_b, agent_a]
            rewards, statuses = play(*pair, seed=seed)
            mine, theirs = rewards[seat_a], rewards[1 - seat_a]
            if mine is None or theirs is None or any(
                    s in {"ERROR", "INVALID"} for s in statuses):
                errors += 1
                continue
            margins.append(mine - theirs)
            if mine > theirs:
                wins_a += 1
            elif mine < theirs:
                wins_b += 1
            else:
                ties += 1
    return {
        "agent_a": name_a, "agent_b": name_b,
        "wins_a": wins_a, "wins_b": wins_b, "ties": ties, "errors": errors,
        "games": wins_a + wins_b + ties,
        "mean_margin_a": round(sum(margins) / len(margins), 1) if margins else 0.0,
    }


started = time.time()
rows = []

# Challenger against every rung. This is the part that must be measured fresh.
for slug, ref in reference.items():
    row = duel(CHALLENGER_NAME, challenger, slug, ref)
    rows.append(row)
    print(f"  {CHALLENGER_NAME} {row['wins_a']}-{row['wins_b']} {slug}"
          f"  (tier {TIER_OF[slug]}, margin {row['mean_margin_a']:+,.0f})")

# The rung above the ladder, plus one pairing that ties it to the ladder -- otherwise
# Bradley-Terry sees the host only through the challenger and cannot place either one.
if top_meta is not None:
    row = duel(CHALLENGER_NAME, challenger, TOP_META_SLUG, top_meta)
    rows.append(row)
    print(f"  {CHALLENGER_NAME} {row['wins_a']}-{row['wins_b']} {TOP_META_SLUG}"
          f"  (tier 10, margin {row['mean_margin_a']:+,.0f})")
    row = duel(TOP_META_SLUG, top_meta, "closer_cleo", reference["closer_cleo"])
    rows.append(row)
    print(f"  {TOP_META_SLUG} {row['wins_a']}-{row['wins_b']} closer_cleo"
          f"  (margin {row['mean_margin_a']:+,.0f})")

# Reference-vs-reference comes precomputed in the dataset, so the default run stays
# fast. Flip FULL_ROUND_ROBIN to replay it on your own seeds instead.
if FULL_ROUND_ROBIN:
    print("\nreplaying reference-vs-reference...")
    for a, b in itertools.combinations(reference, 2):
        row = duel(a, reference[a], b, reference[b])
        rows.append(row)
        print(f"  {a} {row['wins_a']}-{row['wins_b']} {b}")
else:
    baseline = pd.read_csv(DATASET_DIR / "baseline_league.csv")
    rows += baseline.to_dict("records")
    print(f"\nreused {len(baseline)} precomputed reference pairings from the dataset")

results = pd.DataFrame(rows)
print(f"\n{len(results)} pairings in {time.time() - started:.0f}s"
      f"   errors: {int(results.errors.sum())}")


def bradley_terry(rows, iterations=10_000, tol=1e-10, prior=0.5):
    """Fit BT strengths by MM iteration.

    `prior` adds half a phantom win each way against an average opponent, which keeps
    an undefeated (or winless) agent from running off to infinity.
    """
    pairs = {}
    for r in rows:
        key = (r["agent_a"], r["agent_b"])
        wa, wb = pairs.get(key, (0.0, 0.0))
        # A tie counts as half a win to each side.
        pairs[key] = (wa + r["wins_a"] + 0.5 * r["ties"],
                      wb + r["wins_b"] + 0.5 * r["ties"])

    names = sorted({n for pair in pairs for n in pair})
    strength = {n: 1.0 for n in names}
    wins = {n: 0.0 for n in names}
    games = {n: [] for n in names}
    for (a, b), (wa, wb) in pairs.items():
        wins[a] += wa
        wins[b] += wb
        games[a].append((b, wa + wb))
        games[b].append((a, wa + wb))

    for _ in range(iterations):
        delta = 0.0
        for n in names:
            numerator = wins[n] + prior
            denominator = prior / (prior + 1.0) * 2.0
            for other, total in games[n]:
                denominator += total / (strength[n] + strength[other])
            if denominator <= 0:
                continue
            updated = numerator / denominator
            delta = max(delta, abs(updated - strength[n]) / max(updated, 1e-12))
            strength[n] = updated
        geo = math.exp(sum(math.log(max(s, 1e-12)) for s in strength.values()) / len(strength))
        for n in names:
            strength[n] /= geo
        if delta < tol:
            break

    return {n: 1500 + 400 * math.log10(max(s, 1e-12)) for n, s in strength.items()}


def rank_table(rows):
    ratings = bradley_terry(rows)
    stats = {n: {"wins": 0, "losses": 0, "ties": 0, "margins": []} for n in ratings}
    for r in rows:
        a, b = r["agent_a"], r["agent_b"]
        stats[a]["wins"] += r["wins_a"]; stats[a]["losses"] += r["wins_b"]
        stats[b]["wins"] += r["wins_b"]; stats[b]["losses"] += r["wins_a"]
        stats[a]["ties"] += r["ties"];   stats[b]["ties"] += r["ties"]
        stats[a]["margins"].append(r["mean_margin_a"])
        stats[b]["margins"].append(-r["mean_margin_a"])

    out = []
    for n, s in stats.items():
        played = s["wins"] + s["losses"] + s["ties"]
        out.append({
            "agent": NAME_OF.get(n, n),
            "slug": n,
            "tier": TIER_OF.get(n, "you"),
            "bt_rating": round(ratings[n]),
            "record": f"{s['wins']}-{s['losses']}-{s['ties']}",
            "win_pct": round(100 * s["wins"] / played, 1) if played else 0.0,
            "mean_margin": round(sum(s["margins"]) / len(s["margins"])) if s["margins"] else 0,
        })
    return (pd.DataFrame(out)
            .sort_values("bt_rating", ascending=False)
            .reset_index(drop=True))


table = rank_table(results.to_dict("records"))
table.index += 1
table


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.4))

colors = ["#d1495b" if s == CHALLENGER_NAME else "#4c6ef5" for s in table.slug]
ax1.barh(table.agent[::-1], table.bt_rating[::-1], color=colors[::-1])
ax1.set_xlabel("Bradley-Terry rating (1500 = field average)")
ax1.set_title("Ranking — your agent in red")
ax1.grid(axis="x", alpha=.3)

ref_rows = table[table.slug != CHALLENGER_NAME].sort_values("tier")
ax2.plot(ref_rows.tier, ref_rows.bt_rating, "-o", color="#4c6ef5", label="reference ladder")
you = table[table.slug == CHALLENGER_NAME]
if len(you):
    ax2.axhline(you.bt_rating.iloc[0], color="#d1495b", ls="--",
                label=f"you ({int(you.bt_rating.iloc[0])})")
ax2.set_xlabel("reference tier"); ax2.set_ylabel("BT rating")
ax2.set_title("Which rung did you land on?")
ax2.legend(); ax2.grid(alpha=.3)

plt.tight_layout(); plt.show()


you_rows = results[(results.agent_a == CHALLENGER_NAME) | (results.agent_b == CHALLENGER_NAME)]
print(f"{CHALLENGER_NAME} vs the ladder\n" + "=" * 58)
beaten = []
for _, r in you_rows.iterrows():
    if r.agent_a == CHALLENGER_NAME:
        opp, my_w, their_w, margin = r.agent_b, r.wins_a, r.wins_b, r.mean_margin_a
    else:
        opp, my_w, their_w, margin = r.agent_a, r.wins_b, r.wins_a, -r.mean_margin_a
    verdict = "WIN " if my_w > their_w else ("tie " if my_w == their_w else "LOSS")
    if my_w > their_w:
        beaten.append(TIER_OF[opp])
    print(f"  {verdict} vs tier {TIER_OF[opp]} {NAME_OF[opp]:<18} "
          f"{my_w}-{their_w}   margin {margin:+,.0f}")

print()
if beaten:
    top = max(beaten)
    top_slug = next(k for k, v in TIER_OF.items() if v == top)
    nxt = manifest[manifest.tier == top + 1]
    print(f"Highest tier beaten: {top} ({NAME_OF[top_slug]})")
    if len(nxt):
        print(f"\nNext rung — tier {top + 1}, {nxt.agent_name.iloc[0]}:")
        print("  " + nxt.headline.iloc[0])
        print("  " + nxt.lesson.iloc[0])
    elif top_meta is not None and top >= TIER_OF[TOP_META_SLUG]:
        print("\nYou beat the top-meta host as well. There is no rung left here --")
        print("raise SEEDS for tighter error bars, then submit.")
    else:
        print("\nYou beat the whole ladder. Time to raise the seed count and submit.")
else:
    print("No wins yet. Start with tier 0 (Fallow Finn) — it literally passes every turn,")
    print("so losing to it means the agent is destroying value: buying seeds it never")
    print("waters, or livestock it never feeds.")
