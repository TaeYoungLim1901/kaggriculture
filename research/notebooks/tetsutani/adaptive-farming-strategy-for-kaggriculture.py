from pathlib import Path
import base64, contextlib, hashlib, html, io, importlib.util, shutil, zlib
from IPython.display import HTML, display

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

_AGENT_B85 = 'c-qXpXP4SY6EOOHf5rH$!;G;PNk~FG>!buqAW$I4#~ur16j4A3+xy$EM3{l`*xu*4?|skpIctNuySlo%a+O#wOyV@ZTI!jF!hd*&Z$_L{r_ZY_j!vILJ$Fx^cY(M3<5m(?g}xQU*)4&>S8uOgSfezbtKfzig;JZuFbpL^vprfZw^g!{gyCQktH@%}WAOzA;Th#_jI!uj{dRl9YfMiC7sYTj++xz4r8_}7n&$JaorIFF(d~Ax&Dre^3hnBT`KJE7#jtEVS9XSNZvw1s&0A=%6Cxr5AY!WqY1-|Uy_|QEUR$&_n|5clY`42zdpzd0SbJ<E(^i|Jz#5*h=_tvzwOQ6Hm0s6g`aN-ntT&s^&RA0LxV<5QtR0nIYm;xW4%jxLWNRrYvokvRu4P6fERNef%xrI5w7u!VZ49<MD;R8r<pROl8@s&%u{JZRfI*Ecq6r(s*t8d5(kr?xxIK<w)TZXhkU&`hDVAYtv<!M;r|V)Ji<rjMm;|>#TUo34C=_;LM0FM=FcO%;^oLfOb_3g=YrRdH*Z+<CblZ&DM4N=<<%XMe?6#(OmZD_VroBlD!X4OVXB3R-oe57mU~k-E5S!`Qop711*(7g`re)74LR*n+CFm77Krd$kR<_$6H(V_%y|)0z8kHfiLs~0S+}W+x#su<R8yy4@mBv<>ZB~Y$ZaRya3;K3pvP{pd7EG6wLPD$0HC$M$QQ(MNtm&QBYS(j%ju=f=8r<#7BZi$-Q8o4EWUF7|$c7mAQv_0kwX@PIbVO}AsBNnekRh`+W=$ljpmMh)wg`qU#&AKKZrQeXIlMvXQ3kW!)jX>2E-?XMleHoMfrGM}wOegRnL;+&sn21U;xd^93l%_JD01*3+JR!E4f3$H>!IXY0ZBVwFX%a_W8*G_gv(ufgU-j$uIR4XraexD7QKr{%qj^=c_xozbBJ|_cD}Ikp>0e`lhMZ93a%1+Tu!pGZ}r;Fcqg_xE52x(#YVFMc|jlnxEed?&=81n*ntN_dg(+N*@L`J?sL(wwWG4sG#RrbiNzKxWiCwdRS%&cY2_$r{qMwbW=^}m*-8Z#a0C`x(_sWnmBplIbb2k>vXra?P8WF8>oAj93Bwdd!s8uUjV8<9&csL#lcC-yn_I~?UAuzO<@^!awW8j<rQ0G#4WM=4<Xfb~NT_e7lr^bVLZz22!BlEqp0UbYHVm(r72#wza>j1g5UKSJ?#LmuF?j?aa8DCJfa_7+d?sZ8n?b{BXRKBOw_;ZcBB<>JrAZYmE+{<cuE;LRw$f;^9@3jRJ1Aje$d>k|KTJ_OCes|VT4P)5wEB)&iiwNno@8!Uq*)CjQ*!a4DpcKNwxkdpF}CZLznSQG$K{0ymCV$MMw9YD_UF2S3hSwA&E|G}M5e+vn?eDX{nn@h<AOx4pn(@t5y(+_zZA$=bvjxJxhvmMw-Y=N;F!SB-bR^0Jidxsamf!w2`lJ{!?%V(4sKT#%plTg8{l@YMN0rU+1aBVH8CgKu*wHcZyUgqYDsn|6i(Ez7f!&<3WZ2%uo)Y9+Ust(ZPB#{AQ3Cf){p=wiMC9IY`Pn(osvk=&UV>Al1Xm7WbJY8vl;@rV6kujV379V5Fd;ze=*@BsY7HtmY3w|M$L1Lq=oSi3>FTQ`xP_m)8azpU3uoV7z#Gh&b(!~={R4u6e7vyJ_w`kF5x;u7a|aHUAEi~+FFO&Y>`dud9v2YB@N|B<&N>N)&Z*(w!vLtEMX>0&MIumt%~u2w$nI(b~f!85x`?RftEaeK&}G2AL@FmaO{D`!&5g{426uzyH;nk0OR3^2O+z+9RY&9!;BFJ<%@1>Bf>d6*d+Q$8J317>8zqbDhiJDoFxhj27NAV%_)iX9EL4}dAZ6MgiOFuK9Ola!T=FyaV|OsvU1A$R<g;8(OgppZ4mGkmfOsLR$?>aN>gommU#{hMX>2E=q<yGA~9S^L!nAD2N(xXku%b02js)Nz$s;nCOF26%v8sjP#2TY%Ekw_HV~{`IPFIhYo|$8;*9`!lrAelZY?q?hPHsh2jViWia}25m`B8()9pi(<!lY$)2iL2QU#c#{iwYdRAUd_7~zQNaBQhKn;>C0*A2UNlt4S0pL9b=_h+WEktEic^nDj|Wn2U(tkcf5{$vMl9JfVJsxawbK%9alvzRCfHN~(%qrw~}456)3GOo;*$XXJ|%YL6|Ba2|{D9dFFMA6x7nafOs8f%hiSCY0_(y?UYI7Q?u6NhsU40pSEx4#=9{LmeVxkE=jJzIua!lOMuhWk!OoFGYeg0Gm!Te8KlR*p-j#f%w&b0*BJ&^kMKrl#$7(&yzJ2ahaOs_@7b5M1auHaA~LJ)epN3{Sd)YCuHfz|91egNHpb@(s_PjE!_PqtdBZbXp8QSPMi@_~R9odb>V@umBLd#7HS@h_Cn2#%v4MOR}i2A>A!I7PD)cZD!EHyt2Kvp&)7nbKD3zvv!);lS~p5a?+a(FwLEri<FAX6ekG?OBJ^VLo+&XJYeIE3L1+<av?izZ!U?VoRk{T9`$&7+rjZ5Rp#SZ>klWj7FaAa##1r0KNnY%P(*q-qkthu(ZR}_Wiq2-0D^bMX6!F>ae?~IG(~cA5i5pf%zANFKngrh>D=U6<Ny=3QYpX`tJ+BYsj~Ycd+3A_Qxv`xE_<`sgeDr$3t1~QVJj~L!ZlTN8bJ&Jz=Atn8lEhP3(E|^6m{IW9H!A~s8%rSZPT*P7`DDkvh7w}GNL}622*6QC6jIsuy}KpF)j|YM!q8@E@a~B#vaT}UX(haFH9K`Mut>|b&=h~fJ8|#LCx%eQ!SgZ1C48?YiWZSLyQf#L6smG&&*0cR=D=qh5AyDnu*Z3*O&N6uU2SPwlkwYv&b2d(=3Oq8EdkgQKB$`cPOjRz4l6-QaDq@f{Ti%GzPmM>alTEMjlG$X)7d&0Y^E5_N+CWIjrHhrY`ko>#S3@M!UJU?RWhk_EC3>@WBKgNeNtNu|8zPT$q*6R7{z40;PSzF1j<3?o4)$tcaM8xTRmleOHuJr_b@3G<W!lmk45*X_*3q(HNcqvA>HHx5WZuUre#JE$UmBUa)-64fP&nE|<NeWI~PTwNqt7w${#uTbGuZL4(y|KFJr``PKv{U9%HRJhVf{GXnEzpM)*l7nsT{v&DFwGOS^&Ii#9|!=Yg%lxDk`Gv2Zb0LJF5VX66I<nSdARg3mi;;G7+BD18mSeOuyPb#I#fS?Bz%yQdbrRH=f*hp;VT}KNt0l=n3TGl*-h^s2|dNRo?0%cIr#>@p#DB^V|UXnNlt|)>Qqz-1mZmA&w+V6H*7~e2Li=51D0~}_MRHH0ZzCK>eqCQ<Kjd;zvqaBt{f`#BNTVZIY6*ui|?J;RkRqezZ<Iu+2j-laNKC{rBp6zmXV=e#-?Z`z(Zmkr0Co9|<t;Mg);nK)zQ6mWBtd+IF$H}-b6u6o*d}(y8xubyt&6y78QW5vEEh3Vo<AG6ujn{6BIO<N*NmL-Toy3e5(#G4ZBLS*7J^^<EDKL~iQnj@K;bVc=rrS{}C<;gLtC5+Z;0D%Y##j@BtssWmF31x;+0`dRpryX-Vt^tD2q2GZXIQat-wfs}or(2njuz++MaktRoJ3tmW&u0}S9HDoN-2dF-U+sh>r*u#G#YkhR=kc!JB1T*NwcK@iK;m|+)bBQxSP&wx$C+CIoiPeP+sV<?jp4poarvyDVNJ2A3_|fwVZxQ<CuxD+B62L+R0tZ&P*MZzUFL4#@uD1LhtMJ)c1x+HNfrlfGPO(G?`5)h`<58wE)xF5YfG1Z%J~YQOsy*f`bb_VLBu(3V33pJxSbYI9iDwxm>nOe={uw)sq&BjX-<at{56L*jaRA(Mtz-+m(Rj%!EBI@O)mQV0{uL^T2B>;JO8_`>Re{sMaY-@&)7pNiL9-IG7r)#;psnT5i*Di!CslwYCno>RO}3Di*_FI@|OlV!()|u5g0_0Qfi|34W0v5kIJXr2e9$M!s1l9$WymWf$iqvK+PoyvGbz7>#e^p)OFW3v=ak9a;fG_!Ya+J)N#FveFZEoWb3-N9jzDHFUzn>9A0zpkL_eYTMT*t9XWoq#JcNE22asa+uF%Dw*e1Q5(atA@MGlSz?sb{wCC&bs<U~$pwR0tGT@Kn3C~>1?jF74QmOLOz23eC-RU24Z-PrYr(1kusF+_^n{6=ZbBAi6aYb6>g}fDmgNjoibQ2wEW}W9R1HvlArn|PLQ7I!nA)rqvo<cSrs2TyOaZPGW=SK66Gf5XDL6esMnkc`;DY4_td(`yR$P-_7WfP^OnbugWwr$9-HLOz1HRLj5Pq?uq^0U+Rxwl)NT!A;Y+^l@>WQLRM@@Z7+*QO>#*7_FG8)ufVu;rFQaG~R?h0EXC=ViQI$&j0gb24^7WrnW(OFvI>sFtfYM`;>6FlME;o1oL>|#tu?RjTj8Ocy`>39*a3MjVte#uN@gw&yUUSz#BY0$x>(*eN>YuDx(9>m-En(_uDI!b9SHI!(SC$tI?D~6EBSg1B@MaNvG@3;Gb50bQjPo~_+pLtVQPe^fx7|g0g)xMix<!jia7xMtc;*BJCm)()pnlY1DHF?^gkhltLz0K9$9EVb3KNdCJV;u(OwbYusfHBAWoi&uIeROJN!J0?l&PZ+1V3p;oj+)NmcHUnLjFj->+Al>tm+RYFNf~uuHZeJA1uti#KD8Sddd3HHeU-v8Y6~<s+6IKa*@Or>5-dI5(h9qVa*wD~V?0M^IExL-vDqd77hh}*9AhvdAI6|M>8}znLNL*hutC4$ET~?4O49rcbJvq`3R)45XFYmgnZqmvYh~s^x>3#Halpq)YLQ;)1MzakD||_jz{2Pe%QhpIJIh@tNP8{H(N?Hx8HD?l6zk9qnZPVFbOQ-2`%VNS5v$^z+PlZZZF`kWB8{OoRfV>C0W-#jBVaBUx<4(0rQ*;svKwyIAq-3k4mXBA8yW~X!`fq7C%p-evxe67mARU9Nx#4ZdMu4VD3#EOrMJo=G36x2K!qKxGuDAyJx$BEJ}?xbjjT-3jH22O>j<F1A{N^Ryl4PBs_fwKaBAd*DP)5dS*$U@j5g9%&bwev<SD5wSjlX;9#Lc-=d3s}&-x)28&h%ERY#sL<uo4&!xn2Y%D{sAsIM=rRGU^gMh76<B0#hip~~3xF%j`_+O;5<Ch>qZyZGAekNnk?YENl&zLVB{bvcaZTDSrM-mxcPSb++FvnvGc#I#_=YAO_IH8<q}*p;1#b`>yo)&7{G*L()p0Z3*VZ!E&fVI%~OByKeIO<EX<Tp4hpY1&g(_jQ*lownzKFj>phAhdW)_nB55(T}JY=<=I*715({Ivx+jSnBkqOR4}l(wF_Urq0p1hNc6{r*VJb4@Y9V>jItLz)B}D+5@2-p|yEe#ngV;%`14L!x1u{`eR|3hEs#jCNpyY1S%$OR{50D+G12uAhd}R#m)0zG%`#lENO(v*<vIC6}#o^8R{UZuM354OQkSi<;{HPh@QxraUY~BL(a;4r6E-h^a*UWMr<+*cEWsIa~wSPY+GI`rmGwH8Z*&+xb3PL2Sft`+eloPS)eD+)}+<(DsU8}U7*Uz!J75CUd`52>bK0bSw(daTqcXMFQ691ZRYyO!a8fI_635S7A-xRPTgMNC}ot_j)2@Ut4<g5O?&RLf*hL2td}gj5vNV)1ZA_C%B|WClMwyMasd{aWy^uM$|(UKZG{CUSW`}zEWE8;Mhh3v4WD5KW`)c<Y~Kl8H-Wev3F7J?7*C`!4FaD^v4Oh5W-O$(c$Fgherv&`*3jZ`nH>@yR^liM4EvrMFovgc{x*_!Y95VbTFWvHp`d}?Q@8X$DN4F_y9+Z^r`TwL6T7?*sWC3}$i!PspxgvKhhupRjIlCDt^T}IdzGl|5@ie+l2>tJ=4`U|6iP}moUvHd-GTln@911UR~8~U#*r=q@f^VrCf~_sMBk>=wQ0FxZCZLB;Oc8s>>?8%7MF<cSk{W?S$7y^xK>B)E5QiO8SQt<fhVS(3*i96WUlRZ=CH}hWV%Jy(N+=LBO`BN(|}8d7AyrJuBW?!Y_q9Z)82Gw#c?<=8V$E_KGc`;tg{@?TRtlHLvk`91=T96sUnnQUmEoVSe%U1$+iwt7v)A@*?lr2#GXh9y}0F$;jumzI3gBVsWqC^u2nc%LXs!D6WQ@l*JQ@2q87R0uC@^>2!;*%^U=~l^mRfwLTgl5kVfiD1h=c6?gKCvrA4sZl>=&8RGc%QTWij8ks?~prY#b6hLlEc>(Dn}YZGES+y=gwt&|SVA`@T>#9Ot!_O^7#ogh8Q3zqJhqV+zIX)HYn3qi|#dC&ukaFW4OHA+Mz)2wo*@@=HcsR5lrUg%(k9`gX7%d14nL6i$LkeHHWL13=TFO4u{SD_lZwc|aMEWc0ArWh&&uH&$fSM>?W@ngh_0zSv|K?1mtm<Oa<;Bvd_(klR9hn+Q3fGkf=yahDq`MgK$B*IgDPsMwaRQDEqf0T$Awd(a*tfYj^S_mv73z&3(_7S(k5K|T0P6p(RrD8h60yUb_C6JaH%w%j2E){i4B6^!10Nt6#r99DDJBW>j1E4djC?|FlYnc+MIhqD8qYu(8xps1<r)YB`u-hZEmMlq6_*j_PnOo8Z*201g-&0sGad@0dY+?erKr1c4RzU{=+#Zv@IoU22#vDjfU!4-ODM&`^Y(B~d{ked57p---$BoprCW-O@XQ*_S@bmsk?kJJb<>4yPNU3ji&1^B6PPZK-SV!@iY3X@;6xKmuM_vW6IG_?M(p#$myQ09B06?;)=n?CizD`QMJ9Z5|;QDMJPIt8tbJre1!crgWZCg6owYE5{Cf-Cv19itN)`k;Un}A^w1TVLA(Rdy*30T8oJ=~JMh%i{+khuW#VPRHB!J6()t3;^sgh+rq^&$$;NW2cs2mPXuK(4#ccI;}hpkrw_lIIpfwT56PiKDr1l<P(91g7kEsdVwhT10S^UxgAess*(U^8q5D+X9XDXQSD+>Ltsmsaf$dW>?y-z9DqIj4WwP3^i&JF9kPN*JCYEOb2hrB{8N6BXqj`C=1Mlm)HGlV?<1(JI>PAS7RnIxYlB$kAN+x^|VDLfF<7thA`QlR@>a(#akmcm9<x8yaI`xHd4)O1#9I>A!k@uE@`;e)d{v&+k&avLFP1%kXvgK#LOV|CJvkma-j*bAP*NdTeh|!)k>r_i-n6Alp>B=bURW$Lg|gLXtft9M?zuWtyb!I4E8d&*d<}BHl0%$8g3#z(}Xs=MGF}P$GndOyiXup9i*wQn<}-v*~tl(?m~f(joN&L=^`>xV^s$+3DU;nzAw4Xh|zKnp4rTJ2*espkK$3N;Y?gwy;_B!oIIH>2a{yITqOKdvSz9>clDveh4=syX;fK+q1Vl2G6NBUO2pl6tJxyb^M<lnyYd3-%rkn{cjj{~EpUd{lyWtuVYS$;LIv$k*AQOra-icCoY&J@Wlu?DZ!?J}iYjr7c!;11vtsM$SV+OzqmWTp70S6UuS7tnre$bs{dBSpfnB?rQOh|&cYK?LmhH)G)t^^_GoGbvG&jmt&(o^_3M&&3h8_?uitT)pQllj<rVEQKbY+(iL2jzOt+(okncN<<X47G&OM|%Z+k#9k2Pp4O(=o$t4R=JhTlPe?QHy5FxxkwJLfuUGpufZB$u@u-Ay*`;4G~~BfCF3Y&Ju&~5R+imUrq;kTU3H!+)t_^qrhD#W6&_6X0?!w9VZzAjJYE6zHbUz0r%;?Ht%B|IhxsE+i|QqezohU(FwccYS$5ld9n*!nJE@<z8p5j&Jn}ydR6;f><~wGPB>L8f<uB}HebY$k+c`)2C&S`XVqM$ff7;xFa?SM>4ZsJtpY&Ia(y9FxsIg9JazDXD@Wl83og?r@Chji7y=lSBuqp-&@5zwN9Z`73~fazMm+9q(a8#rC9<D}N^O<UTBgwHx`>NW2zoe1EQi3_WxLU0HA8}J8q7B>*PjR6ZnfA{EjeGU*W_*xJ8)lu$4h&<gO+*^wW6ZMdZp{E6LZ`dQ_3dk@MhQUSP^3y!<OFP)*QKtTLP?7af?C5JHL`)dMIwQwhqZEm8TTgb_<tRglQc!7}~buCXt?xvSQFnGhwu<b%rmDG~Y56x%QlO0r3~IgeBTM&hgfAxk*WB$snjI%fop!igqeGs#bN7!FrA~Sd<P{aAqBL4PX<`NFbSy*DO_9WNWL6oPx}Z31TLaJ_1$M-AzpnT)<f}ixDlvVWd+^20z@%*iLTYY1=0jiaD;Wwq+-BuXcl5go?X7*Gq{_DzCWth=61xp9LcUFNQtda_|8ydvz#|R0T}zGzbkwTTYt|TEh^FN>b6q9#tVjuy&i%bTn>{2@M*}P}x`45kDt$gHy*;NrY)vKy<7egnXBX{I;vlbpn!PGM?cg7Z@>1#3nSapq`a1Ez#|33d%yGb}}S_(LxQRY(dd|u{&}j6yc{lux9lY)HUEZp^CmDts-4?CVUp*BhBNaXq)wb1j>bYmcuh+mgG?_@;r}sI=)-Msj8@QvRZI(k>~}#02lHQP75l~#;T_4Ea}al3EbNdo3WQqx-Fn`ia_DOL;z;!#&_sY;3d{9cIZr&>c|O~X(h%0d;u5(eGSblTP2nwVdu~iKmdum6KIv}jm91;NKw4f2W*b`N@pU^UA)coL^U!tK~h`gNFmk*zAIygTNKlxm{D`Khq1eOJS-;Fc8p^iOc6V5vRZQBPMbn}9lBRT2O7uyt-c7R(r6s=F}uarit23ffap&}I17bRoq&WZ!Xs6k(;x|1MFAmTeM?^1<y}A6ZpK|GUjYPVbM%Ov@g~X^6<{vsuvlz4W43O~^CU5~86=D(h=wA0So8?S1rj}#cNo2nCaR1x_*ih*m8?`HRjjAeRga$2SbrO>ojPpI$w>7hTI_5VR*p-(XufGrY+UKKifD)J(p9(s_`cp}WetiU6tqXhDhKnyAnFR+tu0yLYRRN?aVA*7#+rd`8<asUD-r_53sTvRfnf<(rpE*zqqsmwxspt1>)PxsiotXRqOxKWKC;#&R97W+#Shrj-45_T5Yw=B6y1R^X2TAZx+}lkH<qeTab(Qe9X$2a3K^*y7gm^ARD$5anHf?>$@NF9;f34XG~;}3;;7C>$fX$IKoXS#Dux^-oEFQmzMa;FeKt(H^I|gWLaap*c)#tY@D5w}<9=v!;Hcj>eXuVK38DkeNYx!v5H&UdB!$}Rp1L6z$Xe+w!p-Si@<lgFBb&$PJq6UpEE5&Rtg8sc+V&<sK9Q?pC#nJ?3_~I$l(;|k5WyHu2D6w7hOAl`EGz6VEy^68sGVLcpZY5waD%yQWXKe+<|=G23{s>9d^&-aGJ%#|5~0$3J_u)MVD6k?*<%N@GSy6*j49JqNpIS-t6?`FCKU?qWT6N^b2IYYK3wC}DGHHT84AUQC|zlZ#KEi#hIMEKO?5I$@~T@gFciW14DzkHDytA6r9@{upG`Z&(yP6F-px2^1h*>zmFMV22o@BmAsyGVNj}XG))>usf<oF@#;(g!3W7Na4)I~K;&i-|aHP*WbF?=DLU}t3aiO+=m5(kHDk#e_hk(A(Eigc_$>p{%eBEBtGzj&fl0jhHPCHH<W@*<(ldY&~Il{-|G|IM=!lp764+*3g^O0#Pkr!bDQyd1hU9-#F9qPuyt<cc~p@w`u4I<u|jr)8UZPt^mzYs{=_t|pQ6AWx-gjp$3iQlaqhVgDmo0E#^(?dHR`g6{hSnkFwl8nv`yRfhdZ|}_YGB%h{^W#2_2^(!a=mWUtV_m%fmYSePeICmZL|5z$hY0Nu34OVpm};IW>T+zhpy_~L^#`prUaia>j?R`ll<Pw@SNPdvY|DLDr^r|;drM74$I&(qdJs47NZVTSu^HXjXhV6Kld`<1*=@NVQL7cP_PlwPbnQe(aAn}jePIsmR>88G>mzj8jdacC0vwcBWv-NiUSKTxV6>u0zHLmrzL1VfP+d@*Ar|9u5yN0Snz4yF#1Mle!V#UUx>eo*ZFjj^)_SRI>jHywO*jPX<j8d5S>|`#{>qLvvL-U_4yg?{W`s~3PL&i06D7lGS{!lWQ0N4MRhpT#$5^$@2@-DXGEi8f4Xu-m?^Ic=lSwhzSXcyzyH$HY>pjPxf=n7`ov7y^{mC4tR#6TL6R}{kQGa32>B&%?r}o-bI$RelH%LOzT7(aEe!6z6@h})Nt^x5dQX<TT#j066lsbJsahCRiN{3^r4k6glx=3xswM0E1vR*pgFcT1KLws-NhYV~KI?Z-8wCC$xslO^=Ytg4z8m9Sqkmy|1i3_mrgG8Amd0DCnToY+DqL#vvacd7So37*8dKr*OkdD2K!bD!z1B;Yodz9BPD;w(}8N)mq5rH+?1o}29RALS77VX^>%2r^SP?2O#J812k2+=O4m+QElO`smK+HOV0VGNP>;%P}t^u!7^Nt2QlIidzB!b)tatO#++u9xAoJMS~J*%AZVTLZa}=j$SmCVran{V7M%4x!I%wG{+TcWH3YY{?JHyd~_C7=+g?aN=!2G$g6q=Vs9~W~S>d<0G`O2F*4#Q{#ebt-x6(xHE#9tG%gQf|?5P!E|fN^rWbYu0#YbCars=ljJ@vAyj7RR=jpL-6dt#{sKH7A^rITnvwt|bvl{BjwD1cK-9$6rjBjpWjM<0)_RR^yMR9-2J(F32g4QNNH}ZZwFMfOev-Gl0~*m6Wb9T;ND%BnD_Zrlm~qn~s!h~RwwUG94lGo2V#Y%tL&g;!MeBZ_0MLnrka^;cuny-yeSO2jOpVQeWm9WNt8ua=G@Votbg`_*#QvrSuuI+^LY}e4842OZYE5sTEdehiMa)5CjoH0+xAwl(GDIW-QanhN;r?0`9I&kq{e|u=$+5fyReM+a5=1G0E^gCHu0Lbc$|<YmY^kHIiI4>|09M!AiBySNFYtDhYA&gCC4}oWgN3OI;k87uZnw}?Dy2w4R$@m)M@}WTjE#@fv7iC!9Vf{=-op`IwNNKmZNx>C3;j7&`qKn2doI|`+U9o0Xe+Mm5aVel&w{a2&OE*jb{%gwE-N$vC-#U`rekt9hPf0Ud00wR1069GQA#??Bv^1V5_UjNvW9W7ZbM;2rQ(XB2P>H;L4RbqFx;<~6TZUs;DM+l$x>f<hR2MSe#-djU^Qc+(5pCMJc$gcnoh}#BWyZO>}qCBIff6N3ARcw$Eoqys4c8TB3eh`J1o!Vc$bIErH+fqx>zbD+n;7~5z6L-4iT{SiaLE;%?JJ{ZB<YN6uHxC;ix*yHM*PzL{_^V7}%P$dSq`l1zI+4<)P2{BO2MtW@i!9@@>Q$dmy2k&>G4;38wmO#`o|FO-ovxt=F6og#=)3xIQvWHd@Qyu12mvW0W9uw$l>CB~8t@E(2P9xvH!h-;P4^Mn~1*Zg&}RsA$rh9EZh*GY6hEBe|a1DtA*+jw6(Eriid~hqy8-O5V+PoM2ce(|4@0M7zRxBQ1ecpTqvdXE%~+sDmwCD*TY@5);3eA{{K;2{We`1C+jFtuBQ13Op?mm|WDZfm7;A=CJ`cXEX-d&JhIHZAY2!pa=~&#Wo6U1<3F=MAd$xp{Wz1T<HCbfW>Y(i6&-kJ)v|#hk-cW>{8gq2ppP15dQY<i$8ADxX7(r-N?N-%C6q-JC^?nV%^NHn<nMIOv{MFB(<{a`q1Y5*Aj)Bho*IX*}!~r^VjkDiz2sQV=r!Q{<y8<(;B=T#Bo{!2miP=tx%85+ht%yX8i>C3qt<54fWKw@>`=wH&*@d>x&sf<I0QwTwO!Rt1A$w|Gc__o4;OU>okAys$PfHUxL`#e}-=AFC;EW;(k%*Y!L#S&pQXuZ5AnFeQ9E|2nFsILHnHoFS7J>KNUV-hc@eEMZ#wUElG=JEePE&1~1X<o<jl;i-)uzjt-~0U)KSC#I*j{IV_<EgJ!|`{0{UZk{1LSvI4)y?(AqFbU_335$tB7DD05~&JTq=j@*8uJ}oJ%z-qL#-wyZ<CC|U!eE;J%bK~T;X0DnA_LooKJbj?+{@4vldv<8H8nc>)-^z?Q-jDB(cz=x-Qwd2Ok<6_;J}|{4tjjBGrY~@5bSu~DlHSkWQ{h!Jz>@SWDbe`we%rI9CpuqZNh`M`-akM(^5q_uJQPKRVd-Cj+LIKQhO{K#4snU65BT39egb%Y?DNAkB(;J-uVw7k%dM~x>%2&UT42uwt(HzBh%>8J0Jm{!T8)5Sp8-G8>+EvxSoiGEm-s)thZ8&1dzF@D-iB5fr&V*yz<;j3ey{nY`RDs_G_{gIuWm~(GUKwIgw^WF%DvEfu<k{mXZdZGTS-lr*I>PgSy&Ihzt}@Q?C@VKsBx*8GpK5=^z8iBiW)LDnyRk{nRPj6rw6@Rk3xR|mt&#6t$8{(+<LH6k7Zuy1$ye`)ooCJY&ac#u)>ROQ@w__SBt=pgLaV@X`>(E%dsri(*|Cxg&q#XNwW`DKd)7I=oR4|L;S#b4=?t3Z-1DUeRXSlR$yLl^q{a_UHMk^>Z*RM7eW4Z6i3$0fBv|t|9JM5mw8c*PGnf8$);!I$MNP*eV;`dUF`?|a;*IN9N5i%TKzQNGh_Wh&-3&I=|%m$Mr^;~X+J|h@cH#&(T^J)o<Fk7{rLGFm-7y1Z{FuQ2uOB)xbNdOcbDJHsBNE>G#`$0u4;q#_4~zMUtidI8d_=1Xn~jI$BBC?oJMY%WglORaan%xsnG*&Z7j2T!N>iIgP5LAxw7NtLG##)uFfGIRvrL;`c#8D$o?g)U#ve)KLPlDq(&Vd<hP!A9WS#Z8IGp|_xB&=*GFclC)ArZ0&VSe{T@*L_uHCLudG^@u7DGB)n{**IJXXqnk|m7o1unV_ZVLQ-jCF9KYlu5ctPs@=*I@orv|O&!_}Ls+UL05kK7y(_<A~&9(Yc4TgLT??=Jb()%_9gZu&81*w3)GiDl$_MbYeXMD>TGU6Akoet$T|{_*MDKfTpEF=)2jkKEL!JfU(g3;UtJtZiQVT-P5@ytBXh+veI+J#wt;yCb|lgLiY><bcD+<Nlv&)czeu?&p8}&k6RYPv^IE0D599x3&PfVbq@HZSDnDcAa^<lWKAGz^?afo?NxtSI~u6UGGO<U)6g2^r<H8{^^fT?&n?3xjFGdlE$kV*F8RmOS=&I=0+Pv`1Q^1rzWYlsmJ%T&qd<!xW4pSKOEG=ar%DaJr8}Y714jLY8!H0`%jHf?e)_^f({hkYpTQ3n#_%sJu%%8e&eInM>yZ+=C8f>zrHza=tUbV%H!0t9*WpKh_g9Aa%mE0-YIVQcwE}h<tUzex&K%n0BBU%%kvG6vwr0M1Ai2em!HKXA0N?_ug=xv%iqY!0qUNs9-Q=u$bRU@10LA1xxgQ}vyqYgr~L{LIIL){rgmSf?W^-cG*@IrMU8jEFXyK_vsioeS+Bf$chDhs)ZK4zF?4n-X8@W%MjYi{R9JTpPf+SZ+yVT!2lnZF=P1t4jrVD4Eg}uIULE|$n>{AyxHb9)`V9s(DH_l1x?$tfx{rI7xOf77I*QE^qw8kf%>l9KbQAUV&4X*;>do64>OrL+Z=t^NtNrus`SXue4fi(~p2%7Kuab9mA4l3gDsab>oij#*^x5~CE{%bFK}k(`aDlaH?Mc;e;~l;y@OKlf;NQU?3ph!?*pKcR`E1Hf!(`9{k~RC(8=pf0KV8gdh~2~)N1A`!UJhq@S{O(7_3H~#oYj6vBfpAT$6HMp!O-;h!LxxV%1sDWPp_%*eJ|JzA~%<)*=N9;1D&yPgU!(eJ)E_9a8M9_eNQj;-pJkR<D7=U?&s-|7wW-_hdlHsAMNRoRzJ>6t#x5#2i4y2)HxlYTIC!~_`_T19NZM}0-m)stfUqJrAjP1P2=>{)wE&8{pWv+<ry<w?`it#s*W(Ok8FR3?p{Vuymlgg<IB~)%Q@3!)^8+iuNL=f*M(k><<(wxj#ykSPUE=YwIePd0MsTsE5hqL`}o&h_-eMlx#R>rjEkrVgwBrAQ2TDngAl*k@9+Z?9ajHHzq@TeHV0@tpL;~kNpjUXf;jh0?xvoci((mg#?g7GeNMgMyS))Q-dwF*4$;}ajrPw&w??e)Wa&<TUR?;)UY45hj;5&>2O<~^*4drz15R45xuOQ2?{}6ht;6#A;csl`e=e?luNWF9vsrr)A=Xb`?Tzu#9sgKA`1GHL_wv9por(0n<n;!LJ;DtZ*Ds7TP8tFn1-t%qPz66iJLvemg1A>4dr0-7S|j{bBuO1x-u$qz#`?}a9EkfP@O#34+|T`V)q49t(ocVusiphpTy=dGV*J#TdUf^VtRf0x!>>J=S|rTc>(3u9Ii!iMkBHTm|LL3=vN)|-`8ayhh~EWQo8Iw`?gOX)I(|E9!ef+n;ar^JOyKI}%d6i0abVfCZ<2bB+lc-3FT^W5cpSf+ap!@Y!jom=<=J^-G+!TfX`s}C-nn{tKMLNDg8R`%SzR~7dOff_I1T!%t7SvNotGR|L7$F@HwNI2lE-AvKHGH+hI1=95_2ELzP*ez4g>iy%(%#w9m3x~?rfx$G}aDisJ;L4X0IIgYY(RGK1ufK>NR+7@lG3DCeoUJew9kQTmBecd%3Ei-XGxO8Sulfm7HJ4Vfukisg>x*EZ2FAc0sPA?szPn_XATMBhd?D{^Tz1QeBtCyQ9K^c2`dh2YBG#|8mKj2P@7fb2s(VtFuRYGF>-BKV_O8Ka#muV_zFfb>Z5c4CB$UeZ)XF&g~_}FCLF2580w7R{L~sE%fpyNu@`P#VH59*A?~Ji)f%x3dfAq-Z5%Cwf*;#M=R5UaCB(RV`}j*4u0BO=XdpAkNUKyS%3V@VLKz(VJ`IPf#Z={W^u|8HNMB)>Q@cv4}QbVPvF0Pd%yhBMLVth`IMS2_kila2l$s3@pO!<xA*JsCLFHlFTJ*Hk$I%~MGEM6hoAPOX+Hk(KQQWJ8K6Uc`!>_}$)5{B-Ycxu6?h7OFUyucrhShomDI|LU|&@F{*Ws#A$&Y-@aeJS=YJk@V#A&Hd{}>bgbSOewP|R!y2!mh;KBon9}lw+H_|-Vqj7k6bS}@>uz3zWFjj|UM@rT~$Vu(h#Qa}0<SEjAq|or@?a6-pP;B@=p;sSMH;;N4wMhR^RrwVHcjc2u810-KhtXd_x>I&Pq@6DL=E9{p4DHzl1bzj*W)|IxyvS)#{b@GxAwM6$|CgNls6sq&-2)~)qI4Gnopa-9@G=}aWcyz~#<zFrQDdKvyGxdzxrcX#;x2i4$ebGcP~$Rjx@V|E+Voz`_lNmG_|8I;0}tF;yNe?o1|K=kg-v=0;(<Wim+XEM95;OxxBIizSlB_V=a+@r1JN7T^J4eI#JhxTO_^6$52*j<9QMnr$IFes!LF8h$9g2H{?)bDp7sOcyt;b4I{Io)cJK(Y4lK;;hh%+#_o?W5b8~qcM?BvgUEE)Y+@r_5G<zQp@^K>Q0rsbJAM1Y?hy$>DSV#7~gLD|bQ-_Dqd+dK|hCluX1U~)oQ^)b>Q8z~Jkx7T~!(Kl%&`l70TQl7un!L*aA8@-!eElyu-&1h=yUhGqcJY)8W1F1oF&Xx|yx4J@7lKIgH1*=nV(Nx<yHCLFU7qVha8n=uZt;G~KFYfA98O|!aPDhc(p>hd$Gnt%8S2xS;%c%^%?5jge5wsUM09Us_Iv-LQhZS~Je&MOTHud|kPijAJsO|x5qfi8QamJQ?zXy*z`XR(w{f7@&%BKL;_1)JtiO(L9X;F={;Y-M_rYzm=+U_Lp2A1Ck4Ci(cAFmp*&i@y+7xOicWC}Ji2YgJa9`~Hm({fYUsTZ!ggKu3<B3l9QQw|{UNuY@W%t#uJJ1{J6gZxjzV^kf=KdZNi30;R@^ui$3l;XTYW9=j+CAofC2?|nMDo6u<fnE)cdV1<e0_eXk1zJ#@QaHo+J16vY%cdbN9j}^dV43=_W<h?*0#qoUwnE{(19AO*1&$#^iH&{9_g0)H#<JA<PHV#17&}a(*G6l&WfIAmBZ6<ZZ4~zO$O|a)i0`~**Qxbx!|4&?k;*S=SP-kzQ4ZYhQq>R-eF^%0-3WE@(Hn1^0}UIeJC>?5&m7d(7v16c+<xU<@F0fWd-W?EZ063@R9Q3ci@hdv!7YlKmJuN{OXu#zbI}!d3((B{|18trA|hmQHTfLzEg&GoO$eAx}(&+YJ8mKKE9yX!HZ89`Gezye!8qDHVN7X#nJ52^8BO^<pKuyp9>53D~ofRB1bR#U$#AC$f>>Ac%A$`Y<byp6)}7I*m$>zqc`$*H)hCq$FE-+x831OmKzoS7}Nj;=x6xon=56vZ@zEdJ$tHsvkUic3Vbuvo@mAb#RpdJ$=v%47ku@N`aUzFFnxyA&Pnu!>206fs($P1;7e|o?^;>wEtibtZ@14pec(Tz0G~^K5h>91muI3x&h=a7eK#H{{It6s-*j&1x9_jF;QX}@qUiMI!-re$yE%SVl{vXH*WkAeuS~uXw=3qG+_K++FZ)9tye@r&yy04W!d1-nPw8nn*t}O1RbXF#Aa7o-J0d+S7AqiAiDHN(lh4*?C3uNEb>DBqcS~XEx8|UsgV!Gx<Heud!IM9?Q8Iz?+b7)TcXUC>x%+zld6;DY2f!8mee$(WWXOj!_=nucv-j~6g?oc*#n(Bo-oBOR-=2ps3z-8p!stw=UO%6`&Ho{|oxb@tqu#!LtEmg5Coi(l+*O@tv%hV&`(_TX*H~+bjyKB|y8C7U*o2~K<?DF*^u0X(=E1{nV+ia-H1_u`x>I*J_|F*81rO^8Z&Z*1pD&X)ArF7(Jqh2E-KTu-Jzfrj=Yh)%keBa$hjzZpe^W0%Ut6U4t|Y&{RuS>DVBR9`1XsNGGcqCR5Swdn`rlfXVoaaEdy_t0JbS(SV9&sJ*Te=)wy%-bPRw}Z{A(W>EYhe~JKoE$;ydzh$$kwN&b9jfOGcJY-PcgZTrJ;fa6FD}YF(vdq;<2@i(i`Sm&5C~)Xm$SvWgZoFnaSOO8GA=|JlGXhoR_|_2m6pV6-s%XO|(jyGe%cCaB6j|IYSMS9)eX#b@ZE_jZn{>zh%i+F$HGnLqog`tSSyyx(R+$Nv`3zy327gwJoEze9G@YvVbmWD{@nTFVha7#bM;K1iNwhS~}K9(^{SO=i34Y+?b|<H5VpW+wHYz5%~NN!iJWmxY4q49tD$y?gR<Mlj+xqv}Nv`Zv=XXfnh8{o0zn<K7}~fv0c!H-pj3PAh)t%-5l;C!V|R?~LweXWkvWbn}1U?sw~^Yh4>u0kgUQVH|%Q*ni&$C>PmX2K}=Y+^FP@Vx&s3Fh_&6^`RUkFL!47A&gz_Ps@JyX7e_G$*ktK2am6JgV_GUet$Q65)3A*&Egul`4d`puu77?(ogA^AMz)Iq1~gDH9Ywa;%}4BQ}Wx_IC%Nbvq2Y;*EjYX&J$%ec=v7M_utRH#s%`Bi`ma^*sWiFf9WfNKPqf?7w7PGc^xd>H%~oeO01~QH`9>$ynE|a)~zwTVZ<dqM58x`R*p5&UAg-1%X|3c;-&F7s?6W|+MiEekKd2d?Yp9HQrnwl=ZPG}FTbxm_5BQjJ^(rJZp+L)g23J`tDOaX&|Xe_yn=`~+=nvW+0b+1c{teq{pXnaF#Mvt#BbE?3Msn)ef#uD&gF0EXQStXAO@q)Z^v|JfVssmupIXGpMjX(elMTBUgupz_%MN<%)76@Y45Qw{Vqu&B*J~T&X{q*efj%(%6@qL!S1x4#P6Pi&wGCkN{?CHju(_84UI|1z~+AcDfvDI_+TL<HzjY&RPhoaKMP-ah53~>U(de1QT@+<@5s*NpK@_ySiHYkEZ>%xH|GnqXpO(+)Xf((!{jI0=S8Rk>}=qU8O23{9kP|OrT!FCzJ|~7mrq~;(kJ8>4|wu)-YvI9KM??TXn#$b*Ha#OU!^t*_Z`x|X?8z#w%2RUI>EuFb-S@GziC-Ng!%QiePj7g8`U37J9R168{C&K@9V8U4Wa()LTsEQwSTv7r#Mzen>LJ7L+x3Ow&@nSYo|T97iG3jCRj~Sb_G1_9=Jf^xXYt~{^NZFhw@Mj>fxmSQ~d&a{9A`coge#v_JK*$XmJ@g98UY|RfoQei>&>1v)QY|>QiLxWzFp-degWb{Vzpe<o|L3_yLQam3@)_wd8xe$1~iHn;d$y_UJc^2j8Q3M#&=;E(PS=k3P(*0l<53`x~!gtIngf*W=C&eoA`emE-j-<2bl}1j*A?=5ZOF-gwiGmFh!2@a#qp<BjInM;1-qx^djk-n+R!^RxQMX8{m!ak<ax<2<>j0v^#k>~Kh8)fhc&NN%3}kW_C(u6Z%*p~N<m&pSz)IX@HIB#oQ0<*|YG?j^51t(xz3xOkbvJtgf=3m<ks?g`au6wXlxohF{YRsjC-<I#_ODxTpNNgX(6R=Tn7!hwBH;ptt5{m`A-I&}K~pG%%x^u`~6Uv>!GE3W<M5B;|d0WNFd(4pLTQ4AlmB(IK-!g5y!Z-&m!dRBqlpSksuQukx!_a6y;gmQ15P8E!%S?Cwp!BY+L*IMs46}@9(8~Wp-GIL)nzKisJ3GN`h*<~H+?zYaLd_2Jau`c{?I~4A2<Ouh%!tfEBkEgl!rGf0n?uOQ5S9e~rI+FPa;8#@m{ktyry&nI~i$rHC;?uEgx3Afqzq;_d_aq*Br{Twn--)1SiYU;dXusPz1y7Zk^IJU4{IQ$ju{6-{6nxWlvaetNdR~*z+|T{Zj@GuO_n|Pn?=k!NonPL@@xuOBCOxT*GhMB3bZ`IS-DTygxtzy~UU#U!{<Rvu-{QP7>qXahJ3dk|JYCw$t8-ucVS(_zPW$`2HHtJnIKPp#&99HIIsJb^)Q4H<=B>u#?q0SR+GhL#zK02i7M?TupFKbFLF?|=mnr4*^5~l%s-wRwhMoX^`qv%c|Dt61_#0t*V%^sEAiR$B&^o?!aa5D1=G^`1|EkY_sD~e>-0Qr3h3D<vJLiwTi2B3qZ2gm&HH-ahMUyXmxTg7EzWvn<9r5}Rt=Rd=s(J)Wez6P$ez6d^uA|WU?$4H|x>uX*`-<qEq$fZ1Xsh=>)^L>FyT1P;y_+oPt1D|=c!9S}y`oWFhTe$d(hB18)-EFB^!cD<YjeMhH`a0F@cFKp;E@K0`^L)C+c<B|_d6>Mgh}A#h1p#H`G)o7G+17>FIeXsy*<V^Xa4D-=VHIAbq4q4Pa&KkRI9RkBK`5B7@VVdar#HmJg3#K(0u(<G|wU2)A02<$``R`BRS{4&vBtqn=S9#l56Lz`9*<Kp?9zAE?)lqAN<zNBYx{%&)huXBVGP(!3EQLVNz?2gGoKd?98$J3GV0b3-6W3i`QOc9|QDbGgQ<2f5PPE$3BP0+lL;siT>L+c8<6-@BUx7S-)wF`s3j%Y{&VBnP=~CR*$@Ldf9??x8x_CR!94Cd%oM*E8lmIPo`r3D<DTF-~zy&?e4ps9&2KHOey`a|IIn@p!OEihoJurlrt-N*;ILeaW_^A+?~0(Jjv_x%})$!)*efB^!g6BS6fBfbBcZ2)n(xMujBH4y!{}N_xqUqut$BQ>^7;<H1!8J_W-dM`>A6qrSyhrAb1a_{^t&b+olAV*7oJd`A2{3XW(iC<$9G|3nF`5Si?Plg^x79%Y&Q*;5-GfKhpn&%)%v&+7Hh9^6L86sfYWw10G4^oaL&l2I7BDLvp|F0Tu6W=l;Y$KhT4%f0`@V>&#jr<EFXxQSLogrI`^QT5Er*l<zWC`<bUMy??Kv_v?PGng5kC{=cAA|6gm#J4rZbo8~vL{-rXxH#qy()_>4ekEy(-fntxrp=qdgQ6l3Mb%D*|Be?bnuXa8EFW^E^9&WW3kAvTN`72*9PeAW_$MncQTzMA6d3Ko_x;WOq{{4;rt|dD?lqf!4|7$jXb@lq#;c}MqxH<29xeE;MTU|~8miH4E>eG3Dc!Sg9Z@iuNhS!t+YF@*;POVK%1M6**l0JF(k$-r@xXHIQ@R~UAtnjkm;ivC%eB4L62OvL3`Jm^18V>(Fm}^{AFVchCz^naHb5Gn~B?XTaiY|!$ze`pfvrPYcg6WUT1k&*>D&R8ZboqN*k7N&jmJqv0A^t`ao+0w_Li>ICY3}yN<k;m;e*Ncn8J#1+8lpVxE<X$Zw|S~JQO+HV(*@Rkeiy_JOml>KKk4<|X&$^GRj)pPJVgx;+4ZrU#lty2$zJRMe|qdCq}$N^-y4F~-;3uEGx{3_Mev!`f2w1=v!J`rzpcaTE#0#Eh++0-n+~$0UYcJ%lk1^TX7Kla)=yFQ+Hpoa$mcd%2JfsX`W(E?zVu#}@5veRUeg2Q&07(H7%_i6{@kU;6?Ze%qW8NN^!AzQZoa<xHsi+ECP{V5Z~vt8+dt>aryqLHo>aTx`1-?FzW6G<?{?oyV{G>K(EA1@)RUVp@wZ-HeSek@z9xqC^?Sh?)X=~`e<3ITq%pL>S6e|Z$gcT$r#^rE&s6(X4WBxq+$FT)rUjL^{c3UpGIsC;{QN=sTc)1k!E4NxI^RtpAVyzaJ3KT%*mPoloiCTm0T+|A-So5e`Bv{c#@{R#L|@bd_*?ulL}d4iL-YA!Hk(54P3pQw7*DO)KXIn@ULtRwy&i#2rht(D{SWwAMYQ285>jvR<k^!iJR&{U-iPwr4<DZGZo?0MFNv+Uctd0VJb8XQl(-qft*{=1E4$mp%ig%}cSeHoO(i~Dr*8?Eo^ns~3UosXBHn*PX?Ni&y<+=%=(>N-{&v#ApC-jg8RUJ_(fsXd{`6}H*ZvNk{pt6yHMRS;PPnh{o{FPq6Zq}$8i2k%5&xO{+zej4RWvgB+#5cpzbYg59iqO!f&W3%_h8cfu%`Q~*0a}huA4l8zu6$NjM*HmEpu<mzI#TzUv`C+`DOaghUt0TibvBo$*RDjgri%=w*}h!W(Mz`qw4d`h#ky{KflW#*8f<gSGuoJ15GXF<v;2Bmc)vYk3Rvoa;$W$&mkem!2i?Un|3*BWb4A;`&V4MZMSW@ub2gWTy8T8fdBzwJgZ$sOp=&K0Umz)OHP%URat|3IOm?T-deRXQz8f=HZeRq_TJA<f;tY0JjPy&)#!XT{HD49`KAB;7r<us`sZ(|FWPcipVqHk?;wg_yPL8Uj>>1J^Yo3e=5Z_&wclQU_9d=ge{H0rZT>)&Q(YzBK~Nh?1fl?6tFG>SrZ|?0m%mV7e0@Pk^4rZWab)wf34>USEc2Vpn3OeOl-HlZd>mhYd2#>PePil;jac1RwW$$B@V6g4<MrP8`52mmMugUnKd|2&iL`m8>?3-=DRzA`2c<s2a`Mx+=NYqqYQHfqU!;U2P(S!*j|-$%>5m+Calbu)>3{sth4L%U^n6FdzxpHn^G~k&JqZ5=`@WNK=J>4*YJPUoj?M8~JyKvh=mhj{#n*@oQW+i9U;XsmSVqJC{2TVO?_GX59LC?il5L+QL+AUiHeaNy+ebg_e^p=ognu7jvDbWe_+|PwMcN+x5{^#8FY^zQbNva551$3QUw%9XQp1X7!oNCvZT$NES@;S{lpp`Yowrr>)!(uf?{}SMA^%ZhSvBBa!ofTaKN1(a^(ffi?!NxE{W?*PxWHbDFJYSe={MzX-|{+t$*RxN?AQH;66`O6Z(c1ATRQU7PcxrwzJMrV?0;aaGBHoeDHJ{Di`U=rKKNPq4eIpUU%ckW`iJ>P<t7#V>*H@f7vC8TaU{jTXrdACzdR3t|LxD$A^y6|^3OaHo5t&R=?}{0*XH|vvR-=$uB@%EHmGl-KYn&a(pOcy0ZFSA<1fD^u-cEupN_KjA76(ok+|3J9Dnu84;~85zvLnA{qWmok#qg6N3O@YpmqUAMElQpuKC4uzK1mV>VCKRd3#oV`O9hGmGmp%$7a3LzstQZWJ3QnZoZYi8M2~VOXX)t_SI+y%&)4wSp>Q^FWXn6Tznb)_G|dlD1VRGx=GkS!o<(Y#FPjDY=8X%;y~*a68y1jL7-FrQU?c5{9?-yF$?sD@cPSF+v+dCw()-Zx!nKlr}ek)-^gEouCA}XQ@#yexnuLi{NwpV0Kc8Sxzs<`Kh*Z=vn&^?u1E#uv%dwwPfP@Qjfw|f{16*|%+D<ezGf%*=U<XIoJ}D6h57a8?6=`sylx!w*RQ^U^YRNnS1L7=ziKz%{%|S3V2b_z^1Xny-zxv13_nSKi+;<$>5bSQlh=Qoz^fJRY*+h%qF=*5ez8k{umhoQlTI;8@^4B$Zd2=zuZ%BW34HMSyYD{xN&j(Vwrgpvm*4&%US-ND<5yrtBb%R@pTFtc@As^|g&D_*$^)jE)lY_T6n{JZbfWG0TRi@ax-in0zkXlM27iI2f%p!4b-ujpNVROHZ_{Jm(5}2rdcO%@XA64G9vmuO$2acm&oA7wZ7#L^Zg;Fa{I~gD-L>?iWTgJ|@aNMglJ`=PzFho<h;;CSf9Pp97Ng(wyxSWde9IOA{{OyZ|AT$Y-jKUIC!>5KkB{)cyw5}J&yQ6<u?#H3<sWxe%ftUyoYnI1-|Vag;oytjYJYzA!rq;IZ`rW#OTO{^xgAn(T-m<98!X@5P`KU5?%^u=uXb&_dF#L1o$8rN{Li~o{jYSLdZUGYitE&~ZT9U$)fXq`n+f%lP2*AX{bwAc9&34|)A-l8NIk%S|K%=H|26JW55oNGyCMD`^NxBFWB-Y+N>2$E{-^pZy?%01{;_rMAM#&%;}`IBI{!27OHUld{yY4a-aP)j4onXv-tl01df|V83sZjU_EBCJ)#gcL>^%d--Q#{QRYJGi(7n0iuBylK_n+UCUgUH`hue+stY`oECyp`>fBO4lvF~3lW^+%A-FW46(+kB6)jSAK%YFZHIYrgqlza2#eT3&d57ZlV@V#5#sqCBQR<*lD@#gy{Wb=2{w6~4jcSXZn)AsE~b;Br*KE36^cjO(#bSZNC=w-YSpSDB%qnrnC5OVx`NDn@Ok#9=gh~u+Y?{LxGO5^vi{@rSk%g^_6CB!dqC44HR{sgv!-$}0iDOBa?pZ^c~d#TF*X%h8+b%;TCY8D~2&#CyPKR;;5kJiagqCtO4QNCGw?set2DtgqK-&LDGz{vc9I(xg%JXdv>rMQiP{$`ZD?u+;q;=I|YZ&a%nshgK_%i4Q4vTwD$mq?uN#r3dJ+_8>-^F)%%)V!IY%g?Xx%YO5m2jgxQE!Xe!hJ5`nAO8Fde?9PG-0k%rrNnsPKX|0Qc$ehhMWXm;m!1;E-%<qJ^1I&eKM%|WkNx}?@MS!8dU%H${hndq2{L`cjQN~t`V9f{Bbn7ZxaS{hV0<ryM>_nwX5Aj7JQL7g-(^i~A6XLq^H2N@x5D2)03qJK<wZR3aQ)BEn4yBqKj(KA=jSi&_PpxNAi5X910(jY&l%*Nu)o}cP8eN4?9CSTI4~b8yC2_weF5^{Fd5&q=;KileldOh^>Z2D$@Z?Qo0<BQW#~>w-#o(3Hv)S^oDW|;AktgOfAe%+y~%U%Y-xI&8Xrvp5G+r-@k@xFES+!7-H$!vorUiOE|T|7&rdu-yq_!|o?4$ggWgXNf6ugd>$}{(15V%2nB5a1zf%T!S_b<2J8bK3>c2UL`0mxaL-vJszIj1!7VC#v9{6kCAxn9@=Ob_bt(xwYw#VC_)%?8iA8Y$Z=~nKTfZk$-yPs|U*AK&YuDx$1de*kbDAC`s>b$_wa{sV9c9wgv@+rJ5_xHWU$ns1(x-|&h7&-cnx&z(9@plYJkH8m4KZwWw&HBQ}QT!8A&j0f${?-`uh~wXB`tLg$zt@*w=wG5Q{ZCa4{_}Rhev?b)rVTe6%bPR-zfW=a`@cnVc;UqH1G%K`-PXHX_vN>b_TEXF^QNP>$8C=ZJRa!sKXmUSq&yeT#QLn_NBH<wdXSGLar&4F^fbNG!+2gMEDYUScizmt`w8^T&9T?b9J)_Ab1S0nZ+vW@%*szd8_%fJ9^xH7$ffoaPP~ODZn%!`&pzLl_sbbxp1pvV-5kGpHxbXnQyxqa&(O{T(7WMVdl%@vgY#~@=Wj>wC#T+d%2a#znr|~YzRLXk82ZapU%LC(_u-k_s~?6lcSWGL>EHj$u+oiH?|0&&zdXE>KR;JMpF^eh!KBxJzWM)LbA3NDda@lnutMJMJGb{Q`^tSik0#isz~|SOl<H^G>Ir4)O_}>i_K{uXsSbSuy6zkE5E1jn@NuiHJd}Abi+=Nme?r~<>mS}PlbeQrpxqx(Q9pZ7qyGAbe}R&Ddyf8QK|}uf0fc#*k?ikp(Ix*=2CipjqFXNZN5kSf#>Kbk&3~6g@!dJ|{JGBzh|e$m19rrle?=69Pm@R7Z34G}7SG~3Z^I7m@;%+=n|}0dy3fA+#^>pMd6pm3Lp@K_e4mW^#dDc=^~QG+b=}2E-L>znLzkD$Xdl`|p4!qLrTQk9*t6>2GMn8A@`=~@JFDXd>|*cTDgHa{W1nmzd)H3(qJius``9Pi$o>&K*~<rA@0IlZMEJ|Amm7Jb+1-_R`RzTXzWPKX+<$`t`(aDfM|Ia*N~h1BFTekY%fau|d+x#he?y|#e}^g*_|0-9{1i>(pVTIPPyXM3mumU1R{ZWlS#QO6V`=H{&Yi)xO&2djxZOkgzkZ@^;w}Hldq1t`EX*%OJ^fD3<Tr5XX|tZK*aD?nH)ib*Bn*8k?&?8A&t1J9jZM?di@W94ZvXURj8yh^8yI!B<Cw$iw~5|9$yydi&GO+qN6qUuTjLuu*ZZ3ey{A35{MEOIh);pU3)IzjgX04=y_H?|0}gl4{bS!`seG2c@|%x7`(FS-@8i#I_1Y)s^Wp1bf18Z+1>eQ@WZSuK!*_2p3BEIaKOCz3Lav#Qf!b$1d4^}7U3m%4zU*D|d}z?7`+BddtjXL$&6|&uvX!abpI(knyb~Sp)~>(2j^58+KVrdqvEQxP3)*|f7wZv%ye~!F^X@&^QSW5;HVVIa&hzu9rTY(C2k<yi{_<qBJ@3(9-qVLC$o_qh=G{I0zYPC>7}WdO0<yyC#i8<!6W|Nz|6K>VzdY3WUT?S$!218)u5O<U;s5Jh+}>SA9x@U=jF1<a`2l?YA#DGM>;F-1u*h%A;&oIc=i+IQ$}@JJJKM_JiL0K$<9oBplf+f;OWgC87IK$v^~D@G&mj5>c?NHQ*<;qZ=T&~t_wA)7eAI;Yo_4=Kd+JL!e2B2&`J8yX>7z*qUwY6d@P@u{+o$-<zfX9-L)f3lVes~n|1q1^JwFt8`)j%M#O3PKm5ry#FW=;ndZP-wQ6`qJ9=^L>BVWIp&-)#%<L{3IDa-AD|Md@lc&)4EfqP9;J4#_V_MN0y4+VtnMtDu*=uIA%NNGC9f(9GPrWHftP^)U?IjN3gecX(Fv(fWu2=shQT{jcu(n*W3;$}s!h5&6-Jwh@ibV8>9#cdJQN`-gpIX>1+jdv@+0}k<O=*abIwT`3Z?<T|Kc)x~M(Q0T;K(7`v5*^dka7dA*%we@6j{vZe0q1h_IgVF=(yiiEK}<xxCa<eijUXryD{;I=03e3;&>R%i6b{E``ArNtj;;o!YWL}Ch4xBLtl}L+c1R9%dl3(u7RLx!SqG~EyY}H_wF-oIO%Ceuu<BQ~vbuR72shk*O|A$aR)v+<+Ua^t2F)&v_cI78etZN7U~mSs+jlkD^Vcnl^~Zb-A7}VDteh(F6en>#*;x-OMI<C>%X&Dm^O6|}x=24APOcC;2*EprbHav3!MbwK^Q&S&sbPcI$6;rWGvHnF_;4xXA@0!ORI0$f#Y|$SfG0L~mW~Y>5knP$gfT5B!`uaXhpl#fw8PbXhpp1He~OD@g$>>~5;D++IZ?p@g$fbtNx%vxdj|{hlvn{xIg1dCV8wRjsL-wey%SJ(VBfNUhRJN0N^{a?N1+X(i;|_PSb9DJTxRle=@s>)B9}f^<L<O(!YZf3U3p+xd)g42OXd+B&999GAcg9_$o9L?5zGP23oy8zwnV{-=gU!9gIYL|?kYY_WU=NP<Vxr0YJCCs@o>$G*cfL#IP7bUJs`w73ild@yK&KP#ugf~-Huwiu{V2;-RuPm=q}BX#CpWt;QLf0V6Qb?zL~J$Sa`#}0B^=Xh^-=IJ+CrCp52g5GK)O#L}5}<6r@1_A#069^|h}W(kxs<2Z(dh)iwaWw}x2-hzs81AvX9i2ExpN9X5k9x~0LMtYMT<YNUpMTX)U{Y>u+0;DT=h^S*Xjh91|~iO!m&Au<-$E}Da9EUrbGabAU&(}nPq-KEk9pO(5Bm=gaq6fLnLoCEIg1Rrr_Os}Erilo#yAVBJaW4>7d{3SVcxfAXCZmj)G3U<nH<j<>pju0TAuLbg?Nu!fCr*_l&h$ghSAn&U)U3M!qcKYLqH?|`ztfksw+gw^5=`{`<D559THUi1wsBSn$XdEYC1`AkUC<q5Fe{%}kajPFHm4iIs3eRV&jK+;t!W#tyBT^qm?I=bkOFku-rzXK5$R&;vtg{0Fa<E5aX?dv8%}GiRI*FYa7T^mR>nO(DPRDpSUPc#du?pZC-JcKFY==_b#?>v8(pb!z;1oFH4ZJArLz1j{EJP3_!%r6!#t3QxwURuQwcwGGw$?*t#3kz3p*wAyXxJ;MZi~7qfRh)eLu&R?PBr4wvOd*<c4dH|VOugEK;L3v&LlB#AMSNNR!9LnP!J-xsvEFQ9Vds-+_rO<K)nx1gGcNe*QwZYzf%LDAQ9lmhBmyf1zL`I6st)4!o~X$4A%%5I0`~SVKRA|Ry8_{hV6-UWK7s#XI8uV?J-$Vrv_q8uEYTpoaF@Ld7Cs~B`vj*5Q2frv$8PpS=6uutrZE{7j7J8A-=jKiih-gYD7oAQeql)@qRrW04*^sP%w|c&@=?x+U21H$!KGxQoA-Ff!Pp@MRu4&nfabB!}V-mNozc{jm-)kguoZ8AW`RHqGv}uxQuKamhoDmAgMbu!MIc7FyOWk#p9VAju2*Sd%9ZYLOf$CD8@4pK_VO;kHAVrJL2eo-KNT2Ro-4Uix{^t-k<E0LZT~_kI+i&x2dkNt#9nE2bd*J<|YTrO!BvY!TT{ck<Dbfb=gMM(DrdOmC8_i+uSswt|O#g4f82kUGw&wa7ck#=i#iKvO-{T_9XB6BBH@KgZoa<m6_<IuBX_;9<L}uQU%MWggjC+<q}hy*xMW<q3tER8oajbjFG}!=h_B0Ymjv+WUsLl#pBiLP|!htYR0CxUTMjMwRUNt3@1|WIgW{^wSdB1O3@a8bjW<wt|(G(0x^dtclP??SPXW87zGGVWKQ|{l>+6x((#3MO*wg9g`U{W<|XS1%A6ce4N`Kwqk1@jFH`Md%{++5wQg=#ID1e<RPnfyqF{Ad30Q7`6ZQ&IHF|OFYmi)>?YN%$>3D89y4lLPu5{@YYA;CP0*gr0F(#VSKs=Q!_m$2M{2X}3N}Lw#B%8{rkHsdSb7VEo%>eIMqiML6bf_dLIPJDV46oKE$YQ>FT_g)2;tty%uA3y;v70LytY_FrDFf6eE3TUaP2x73^^y=}oe1~qd?sQbJ7_2<=G1WY&S*R!g_R;e+m4tBlT$n4h<*SWr=l&?^=Om!XLj0ERb%5k8l+5pNmnH-%sdntadBG9N2;eteM9V^wr!3Xjw;asqE4A~P323}ZZyg}YsBS}?x3UY=n|Q66$(}1UaXF`xd1D(5^%B@c21R(8){jJ2oR1-<En1+z(9Ly^wzrVMeuBjAw?r+A*1tsSZ&gVv*1MF8ao1H^lB<cmd%_5Bjwaq<SmPwW~M%8?xtjX%$0Xxxp7$q$_cLYWsb)=>QGJnfa#gTZXC@rv!?Ex#$RLAYCRd&nsS=$5DS)MwJTNYv}Gi@t+Y1dX@nAoOaUX!BTnzJ9I^W?rf?>47HEMY$FlVclUiehQoHLlIwGdPYG?zh%V^#CttYd>aX7k+m2l}mDqur-wY)pPd9>6rN&^q<Wi`au{iZZlN5$1#a0r<rO?4OB<mKkPuC!#m?23j2*ppe7<(9y%C7iBsWyQF(HC!ac8cw{Mv}>x|UN7WGwIwaWSSIc@cyG=@YifRST^ezQ5hBrocsu3#PH&e*s3;D@ITj2tCUQ#-jf<}jY-UsR$mF<oNXW9Cp}^0!#`el@p>&%Ke#@>sv8VHcy9HfU35Z<<ySg)4Ltkpmq{3uK`@2R{ygdjEE{EFCHo3?-3<*4l4U`_kQ!ALTZ|Oa>^&!Sv_Wx7qA~mwU3Q7y5t*$gVlns3t2Eodea%LP#Js%9bUACaZc&$}D3K5#j_h^7QWv`q$zTRI>im*!Po`fK5c2%c|4m&f!b{soh&$4DY>yX)odlqe~wNO~1xoJRo7`-h&POE};TVrH2&U9NO6eIr7p2;v50*!2mY*+bwY2}yVpzKe1gK_MxL!|UH^BA8-D!Ww@Dl>Owm<WW!0J3_O$QHgrs}rE1k;V<6a^0ceQL8D?m~_3pI%B#6Fo-&r$3s*i={Qr%#P_?EYv_jtWNQXNAw)KI0oR=y$fe<VJH`l|fYi=d#xR8pY0bLBCctS<&2UUo+I+t`xE(Wg)!<}=DpX57)1f=G%_Tkf3^H)5tr7s+G>FLD#+ZxI@P$C<vW=xS9(5_EK=l^8u9MxKoEynBf&-_Wtl;8MCuNhJM&CYO8^NgKBPG?9vY;D-0B4?q=FZ3=%G4t-DJzOsxCvnl7u%R8)7RvVNq0NQZz0jpWgcOq3%g4>daYsHB84{NmTm~DgJBk^b83FPniZqfa(=}|Gb%K7)+4Oy*}`wJ6<a`%s{2<s*i+mpUADv>m95omYsJ1`7dXyHoZ0Iu8uF)3iSVibjAnO8A<MN7$Bu5Npa`?-Xlc=w&v=MFTs_t%K=DEp(q(^+PAu5TEC~1&ln%3GpIM(*!xHYNtAX3)c5h&LA__rLUHJ5@u>lw5ld0^)MWx#+6fEneAF_>iRi(`(05%lgsFqOdQ6<h4RXHEgX{y6yH2~zs>_mVxY8>X)Zn*Z5x;^iLhS5fSlSOtyRY420XGN_bCgRyj9YPT2a0t>M9p*|M?Iz>g@|`_S+wmZE;J%Sf0-WZ}xd%rPx~?u|Af<&V2CP7ojp9f|AGepGZ0Nz=U9#|C6foWbvNPJ-%o`|bTAiejgas$3%msq^DB>=iiU?8Qh{UBdLmh=vV5ygNORcE5rZM@n-{dmFdb=RPRjh$LF~HZZb{d4@vVgf=1Tsi&aMe!Sa=~nc-oCSsbj-&WX@g$$6D|q43r8I!M`7YqL4cpHHFmf%taG(9ho&jTa@TP|j&>b0h{EUs3A%DnYTUBTQATI!*3#G^RrQvVCZ4*&6O#u=5eF(@&zZv6x||W(Ix+gb2-1_5iDjiMYT?zOjdTI;$t(p(u>m!Q-f~F74)zqvzNj8?S3=J#?9io`LX*eHa4F6?w_Ica4dbQ@zMK=-)M<@DgY8_Z`}*SVHcgjKsNVV6yf$@~#@J(+ZVnunI{g6q^}e?UAS&}ltc9%BIgr|;tqN#TXi4ofnSoVE4$N|ava1Q0$%rGmokxvZt$o;Olub(VtMwVyu1!O`2Pp$sus9~lh!XbI*i15Yg2|1t5nu%kB2D(MTV$UE;OG}PAD{dk1nUiP5>E3FF6-Z(D^0*iEGn2i!eGmx+37|)o6DM|Ubs#_tGdV!u2Y}$_0DK?(O#FTCzi*pK8NHb-JaC87lItbCR41=%kt4gU~2og=<U=KJRG;QcZ$&C0zB49fWcB#PNO=>hT?l`D{Or}aTr|6a^G0fX%X=k3_s{%R?04<YT&u*N4*v%Hkmu^=#5ebS&6RmF6V@6$)>^8m@y7%sFrb*UGp+3J=-*uu1)UddNKz`uKb#}8m{U%c=GJ#j2ai~Y^i`DmWU^&+wE9NnAQwcNU<v9vl2hpZ9t2Fw(Yl4l$n}tAoDuz7NJwdW&>A!yZ~}5h$)R}_G6WmDr3<BO=Qg+<3@tXrtJ!c8tw$T(W}<jgvg>pX@PePIer~$39#W+gUs>vaGC^MfF&5rNi$FMjj?Y6bf>OHKqgugR?7fa8mz0B&D!x3>7<=Shc?M>goKhT#LAEDkvB~7Se2Qti$Q&o8pN)$Gohd)F_lM@#llU<?>JA_7uB{&lweT%)DpoWzrho2%I&kQ8vtx?5D?g22zWeHzK||zVO|qVxpL&u2Z&ttWpI0ChJ9x;95lvj{j8W}8YOgNwrOb`=5cleA}7vAH3)$j9FQYMg`}}%GU|l$8wC}#;<{tc6?Qh*l_@Jq708Y0CRqT8NKb7sr{}pEx=c;8DL6X8=HjHgDd-z;CWJ>)bc8nCVp5UBdrwYjVnLt`2&%@WIvPPWowJi3&BrF3O_C`zf4}W0l7Is%rgaIxw%+7~QG?pBQfZh?&Kfg`?Bs73ZPo_P<$<Iw$OVQEntw(XwJzz(%NcFw6W-RI1eYO`RgPv_T9#tW-h{o-j3Q6hEI38%L9}};v~>}Ylt^Exg=wyihB8T@E#$zB8l(vfkOgX<D~kfR>r@RO0z3<5k|O6t4Tb@tP}dBh>3EAsJ8BBHr`8B7Q`l*t3i92B+Vc~)Af;@dz&e`RWUp(su&Cr4y=F$UV2gPV#35ihT8*BQ%au?S#YU4hA=V`a7`3#jh)t<52zO;9HlJd!F~EjySM?F)`YlH~*2F3mM5yz%vgFf93>yfl+bajHVa-;{<INGIPF`^~kIHs|M2ZL)$Lc84ClcN9VE|K7vFw0HTbvrQcQM7lMZ`>^b+S?}`nu(J60!F>=US1HA>xNl-!Xnxv#nqo+`iwN>yv&hSuP7nl$Vc|aX9tahHzK}nlNvf7>jl-v%rA`$4WXE?zq4Q(C|HY&_K2)=uF0)qKi_Z3u<ZHpBs$K7hr|R+L($3epO~Z79o&q#zc1ahbma~FSJ8^g7q^OJ_=V+W*`|cG-7iA>y$#J3geENdx$RQ=|WSo?M8;gV;zI~T6*H*y<75tD;HC@lAYW;Uk9evgOlAPR5H_TxC6sQv&&1R=^@u$skyjKJwy}-0JV#gIpP6p$3oRQYjgpgovu>McEhoG&cjz<6K9IqsRoLZ1Pko^MfnSRypIw9p(Am@Ioj$l6F{xA-~c$+CYV8Ll-&SL*D;@%<b+?Ct4*=9I%j|^Py)X!_RJAH?^p`zuI8zXgY_v>Sxtp(sXDFaMuan1Eb(hevEy1EeBQbkS8#3xDH|vh+FHV@->$|A%9zWsGep8T+Ym$pWrm%OYUPldeS2vG;?UZ5+~x;e?y5}ae8eWmb!aCIj`Quom6L9nRBqnOGQO`lykr1y>KENeNI>f#6`q_dFD~}hN5t-g5QTaH;F&!%u5uGQmKJ+DS%R3jJ<~?24ce8v4n&&Q`fOQ#M=f*`6~T$z%TNn}@p4*|QVp>-48lt>vC(oWv$gA)IFaUgPi$J|oa)*(JcuLSXdsv;La{oYWu{!uDIs&GeUHfu31_Kf(lU4sPUV`z3mUnkGjBGh1K<nlqKrf|xxJzS&XvKIDLZtf^h$-MZFA+4A&XdlXrqvm@yd~xExG3;sDSvB99(wuHf@CKnj<9HE{p84lXvbRcWas9qAtlGFM+fMZp@3hF<>cWPCOJ_VVo^M(k~L+HW<?kl@q){O)Q$vCgU8Z7CW5ugDbgJXF1ox=Ei~)Y;Wg!k<2ZceRXWmx;j`orBxsd$GfK4?(}OirNy;CYA#I<P=3^}>ru-IRSykR&tc5-cD{*&z(&}cy_D&!5k}rI%Y@6Owe^iSEbw5?9ddH`%i8BpV8=^zPisJO#zBH}lC!Hz;L37*y;rb)m3NAok)c`8SP(^0W!omP<{;c$*VwGo=SbIRsN$5|VjH(TK_1UI4sLMWg!Fr8Be_x#!e-VtSxcLxpLOfh59CWuWJO>f5*mmZ9wdZr&|Hb%qgAPAh1+t%*~6yVSSIAA!mQG2N{VXP4B3{D0b0q}%L!)t@@QpPu<W|@VMP&_&_uPt4HBL#r0UY5Idl+J@QMN{ZDegP9Z%Rs5K%pZHWqu-bLtptY_ja($!-B180hV16w{z<IBlr|5>%H%0M?cd()9#!26~SB0I*`qzBH3j7zQd|4atDcRozUfkswu@@=e909M%?YRa)XnWW`P0S_gzr0?RTm<8atwhB`SMZxY=(MO<@sX=@emZCD$cs9QzKAMvDThg#dB2kAV`hCERzLvE!*m1vtCW~RF7kWh9M!m_qnStKG!va`cFsj>bN^JR&M*LYJ`SK3{chk9aM^ki{o)j5oug$%o^4+5D{6p+nRQyFiK)J}AQ)W(^$&dKTG7FaW1Hvlrw6k^YeGq%}o=jgaZQ0Cdq=03rl(l-t%JR?|&__9w?i8lM-`hs(phD%v_v*#ufh0jKf*b8WrsJu<+!51b^pB41DmC2EZ)N?ZrC(iZviw@?(Y3B&Y`PAgQ812pT$%6LMd9KxlNrH~TTyLsv0#_Ur$_0dn5*QcGfwIlTY`BOB=9_fW(}WS~R^*|i8&EZvjkT9i4p?X>47$`a&dprzP*~PRbsAr7fK=t9FJneT?X~MN!&D%Xb{*%`Bc?1%4%!CD;3pX1c3z^cKohmNS~a4gHDwBQJ1haVhz^6=WNKO@HS|&6<XfB{R6F3keXyegW!V?6op<${<Y-B>pR&*aDq)28Y?IV=Z0Jvm_9J=wwSPL+7teF;MfsU#p)A)(2ID^M+f0Ul^<_WCC-@pk9mX@YMrciKr{W1PHELptP2VrLbBnFlvVm_h=Pa&<LS~5mz`&kOOq&aILN*Q^mvBTcsJ3iskEvzNXSIQAQK4%~UfjUOCJFH40xcrFT00VBt&MAU2-|*MBl6yq5$iCG<W{fO;lysZEVTz!p0}Ai`$G=}6z<JaNnB@s*0&+g!sJ>h>Krsz=`LIFN&!u{WM3DEr`yXDcoL~%q}rZ0(w5{Fkf_rf>_(-u@+xM$BnuiE?b4=my%#mYFbPcSg919SNPnCS%t^h|uJG5mR|Se!&4)#~IWwJcIg}I0%u%-Gk4Bd%d*AGv(k(=*&cq{URda>sL0J}IC>iH{!I+b0f|D;^;NU#(y`V|zja{W#RMwDv_Q3qi<TRSj0B{ytg%6D&D;Bsv3#)YHWxTInqsU^n{E0pdJ&G{hbdAf9UR%@xYFBdrL`++#n{wNLo&v=Bss|eIWcN619nYR+&*v!9^gzS2YY9pHUJ6z!RkueD^(fG7&p9Sze4)g0IT&8EnZmur0eIxoSw!;iYzg@;En4H6a|}z+HNP?y*yvB0)h};DYdUqMmKDa+N1*eRL&l9~A=sjLh}0E*g)A$Mk{N^#Sbg1%))*;=1rbHViVp%1mzv$`8dQ0|5hMOM3Tn_fTPwb1aJrgv1hMAUlCoke6~TC#8e0Kss|%&H-t995J)u&QMPqt00J`E?kypu6C@7nX4p^F3TbBZzoWb&WAM~4aTtLQwA_XGc0t_MzN6Pm{9mqtbqP^P4qTCew2yQPUN7HK<^iSBNCedcap_Sk?c+RQUq#R3TuZbeBHI~y&d4_SFWL-v)UmIeciiwt8qu3(Wu)f*RbC4fu4&!-^@nXA!l6@+jMX(}r#4xz6j7bMwNKGQ|Pb+(6t6*(sL^d?G8A)>CpFyJK(V3|;C5lL?w|GGgTG-lOZAd(~=colYm`-G-v267hRo-QLKI!s)wgtx@O-YyZ^Fgy`!S=7FRCWkQT5zeH^d75Yt}i!Rj7&C@E1ma?hLh%jlQwlD&AUl}OR*fcqoJO!*kM=cL@1km(&XbNI}q-P%GCzFVA#$8YcF?@X$V=u>G%u|RUd0}Un%30u9nP1AGHgu)$lX{O1a3GmswDzR^BOaCn=ASY$rJ$Zdfdo9HdY*^BSdC(ofQJ18P?ssdK{?uDpMyvDg)%=mK8oifZ<9PZfr+A8JdSAv$uq&B5Nq?XFZVbON-jlym*wpPJpIk83G!k2b<qDKAdBwilIsmaQ<FvYT@VWfos-!2$pr^y(jWI4EM1M^)_=WmC$|x_s{Fa(z9V)FAgsvF<Ewd)RY`Wf&PP?nkdK1HGD-DLMt@kv}XO3?q$Gf;p%d#T6zo$?l-8*0~&?^KD)FXWQ?2HUVcQv|C1jwxL*-o5J_2NaGk2<iQ;}E1AFO=P@m#b?)}Zx{@+?9gZO+RK9htGG%vYt4u@MME5JLnv5-ew2c#6Si~h-*9szHVp$1BmF1+ILbT`9rK0hWrwpE#9>5BUYfW4^Vv^^`s)_RhT2>^Y;Yx%9eO|}5Ua4tMkcoQjZLT@Wjv$KWc3B#M{TSrypwiCcKuMbeG#regt@mNLVrn<g1}r2qF+GY~bOWb>O3D&Pa+h;$o-R@(mGW8{6r~np_hg|u>VtJ?F_}q5lj^jT)zCD(3`k)!b+Wdtjl-_na+mEX<3<0%rns1HEgp`fBHb7qc8T4I=EW>(Epk;>{su?F&I&8UQ$aeKTlq-KhpsWQVPm81MI^yZrW(GBQL`>>#{2+zEA5n@`{T|nFY{T*5JYF-vu6m68?xdI=BH-cX>{T`%rRpEFQ9iw2AC1Q-z45i+%Vg~+-(AHytpcT=7}{Q2>!O1F6kObF*N|k9h{XQ#;}WaH!-w-S<Q5nqzT}duwiK@GBQzTE;mXVS>7<J08CRvMNIQ<mdDCF8p$lnHtHi5$ih=oI}!~~mBKGwWn>u)f?<Ee*TvCVpzGer{ARaICdghCYYkhE+(}WHgFWi45nE$M3QBPpj~lH!ocS=e{DY%ycN)>Um~E2)+?<)C?xvd~0hkseLjpjUHWS!t-TPDAI`RosIJMNBP*KQf8JDzk)rE}?NyY@n?Z(PZZU#nm*<P6K?h;)$oMVFMb(anW7sh8{d5dQ4xV8ix+y-7#BzkIl6r2xXit=jMI+38)P9p?dFY?w-@b*-B+U1~TQpg3hs@P0(r(JXwJ=&3Iy$Q-bQZ)yr6_=qmb*Ce4K&G=*iJljkv0i$nv=yW%#o_a^Q5ho{>W&l{^+Dn6X3wV9QSn2yu9e-iVb7UtQT-?}!nxLC$ly1A2I+^g;y}M@Rz*{ww#n~K@^nzFtETP4iQ8!UW<kF^yBDv-$xoZT8mii^U6oM)83R5`kw{7@tLja?H8q%xQf|hh;(~$Ad~$u#(G$zI62)y(prX=D>|&ala-^(vd&dQN1bW_9Qi(<5*0!MM$Y-Em*HTRk!RZo5Md@b52%XSyzvXIv8azHm(@W7<gOZP0kp-Mf%(LrUGlYrBk%cS?)#otv%7SH~E~ob(B*w~hH3@vtY8RsJoM<h`RkXLE10M~{qD|GjBJGLPI6A>Li+GmDqLM6pxjb+1m`>T+v8=j>N>0ruT^KK_UUqXG3Q?%}onv`E<U-~8T!qqRB}fe{?h^&p(VWMNChY4~xUI3BhFp?s%@Sd)nNDHpLQkMAVOsv4(o>FRp~`^hAeFWizuS(iaGvmLixpzZ6#PaM=OMFFyVjXQm)WgUI~!n3n$i%XNxNbyqZG^jhW0`LjfIN}VqQ#+ciLt?027D2PeYUU+O5<(?kdTBe(<2o4ivF7)T*QD3^fm#k>>CkHvqjqpSl|L<}5EK2^hEAAet=zSG%i{IC;~hc(}l!(>Q^+zcGOh>peDykX^6(0uS=l1%r1fgHl<b<J;?udsdrQ(A1Ade~<3L4C{`#ip7JEn^JzoRuE#5%y_bS!9I}(gT2t_OIcUT@XkwL5vh7T4bBni%uDHPbnLJ(r^5mB7A@LAgEcg@3?ZST-|(KX?oMlRJ|q0HfT25O^rSIsOEEl}abC^h6o$YV)Nr6djMyxKGj_#zu0A`OWsHZ}n~%E#IiI|3a%k}Cke2hQb9V<i++LP-ZqPtW){kMbMm!j#!Z>G$OmwGQQDHUf`^ps$M9$~e^4cgeH!bhQXUvkJ%QJSyX->ljGlY$`&2cj!avIpp94dM>C{0yfV*0G_xjdjiooCaIIT6bObJ^#<3hW~bDy@yvZV#A&j;r;-3U*}0;w!wZIfyo|`Ch@#+;v`e916F-M_p;(BGq!6?|O)&g8}bo7F$*ct?&#toSF0pg3w7tEp`gK^f1F`#gC>|LWp5@vHk?uiC{3-V~}iPMmHHXZ%;BHBsvc-z;{!yNWt(|Zns`bOm}6OwVhn?WegdO0uDF?C$h9T@2gAOYzm!Is?=0a7^-<xExoKxn@Va567zacy$tGZ8(CrBLe`MvnLzDvO2@g1H-l!4;7v>LwYhJAy&A1F!&38WJzwc_M{(7TK=3@5fU=WzAyGpYW*?e6IYHGzjE)1p>8wbFm?OC>4v=Ddgr{BmS)+@v61O%J?&W5ut5!o6lJ94zI6G?Q9QWr1volhZwe>;RVp771y9hk*b|#RdYQGm&vdMMnB^J)Uf=Vgf*L~m>NLB#r2r{yB1g7(dAxzei!Wf_k3o2Jgoaf^Jb|_iHyQ5jx>OPwd9qbPMzP)bwfEaVv+*|EFhuM%{U?!L#PJ)S;zB%ICu!s|&X(AWd+Hzw?AOdu?dXgxMX&|AL8s8mbdYR88ppM*>O=q`-B+4cE+LdDNblq&s2;L;q`UK9QeCZ=_+M^qH1xBh;`2Drs?hnxrD83gcR3ctDqDo>Q4e3A~_L#4<O?r-S{YZghtJ<4^b`~YP$2O}$THEcgni(<{It0KsMFwp4gS-=2ZHEJ_<~jn@$|D?rf+dycY3J^l^kS$ph2tU{<C_C5AK8vB{KGh%vv~~_$1)@VZG}~2IpGVQTA<#%_LRavR}QketcDeBhQ33lum1Glz|2s4irF6APfG}fqxX4G-g19_Opx;VZGx1~ZxW>36*27Xfe~IGOkMduHz@*$hYK<%tGfG;_T%##ex=XvvUYran+tXM@bx##hg-kv&!46I_{72w={|0J#-Bt`L}QhmgY(-dGC#j@ZU6jDh|`-=FUGw*WQD#BcDXP3$d>iw>a!<={`C11(tvMo0;7R<i{0>5JSlhIi(%34ZkTCq`};H?<lV%&pWl4<`P%`}_pQ1k-ndDxH{OMujkghS&ob?P{yfv}=g$aJ@7oic%Ce2_+~PkaiOPMf%H!L3&L8%4Q2bs3vAgl`US6<=;c`a__JINOND20CYhK_4yQ}wYI<UJIzUk4E@&7hq%6&_2DNWveyN~s~>E>NypVKcrB;WYp<L*-`KfL-k72Y-AE;RXRIA##Np8Te`Pp@)Y>PdL(?dSV=vd_27vWVy$CBHTVb^rO30(XIBpSzT<yfzN1&VBxN|L^*9)Bn!{zw(z!G<|;4<)`<&$&Gwl^KE?fL+fri4n9Bn*-a>M`1!MRt?vqL>En~Kw`15(qM~~tC+e%)h@ZdSr>f1KU%dS`$;zd!w}V3N5}5XP1Nxo$aeMjs9ghS5%{shv|GtW6Qn}+fd>)nZw8JmNi~ZsM1DH_G76'
AGENT_SOURCE = zlib.decompress(base64.b85decode(_AGENT_B85)).decode("utf-8")
EXPECTED_AGENT_SHA = 'b8aa56ff72f62dfc7925afa4eed31a7ef6d20d98388e8d214bb1e1aceb92c5c4'
assert hashlib.sha256(AGENT_SOURCE.encode()).hexdigest() == EXPECTED_AGENT_SHA

AGENT_DIR = Path("kaggriculture_agent").resolve()
if AGENT_DIR.exists():
    shutil.rmtree(AGENT_DIR)
AGENT_DIR.mkdir()
agent_path = AGENT_DIR / "main.py"
agent_path.write_text(AGENT_SOURCE, encoding="utf-8")

def show_farm_motion(env, seat=0, stride=10, duration=18):
    frames = list(range(0, len(env.steps), stride))
    if frames[-1] != len(env.steps)-1:
        frames.append(len(env.steps)-1)
    observations = [env.steps[idx][seat].observation for idx in frames]
    player_id = int(observations[0].player)
    farms = [obs.farms[player_id] for obs in observations]
    rows, cols = len(farms[0]['tiles']), len(farms[0]['tiles'][0])

    colors = {
        'LOCKED':'#20362C','EMPTY':'#E6EEE9','WHEAT':'#E5B94E','CARROT':'#E69A4A','TOMATO':'#D65A4A',
        'STRAWBERRY':'#D85C70','MELON':'#61B873','PASTURE':'#4B9DA5','WEED':'#A66BB5','OTHER':'#A9B8AF'
    }
    def category(tile):
        if tile == 'LOCKED': return 'LOCKED'
        if tile is None: return 'EMPTY'
        if isinstance(tile, dict):
            kind = tile.get('kind')
            if kind == 'PLANT': return tile.get('crop','OTHER')
            if kind == 'PASTURE': return 'PASTURE'
            if kind == 'WEED': return 'WEED'
        return 'OTHER'

    cell=27; gap=2; map_x=34; map_y=74
    map_w=cols*cell; map_h=rows*cell
    width=960; height=405
    parts=[]
    parts.append(f'<div style="background:#fff;border:1px solid #d5e3da;border-radius:24px;padding:14px 14px 10px;box-shadow:0 10px 28px rgba(24,68,44,.07);margin:14px 0 16px;overflow-x:auto;color:#173322">')
    parts.append(f'<svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:1040px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg">')
    parts.append('<rect x="8" y="8" width="944" height="389" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>')
    parts.append('<text x="34" y="34" font-size="17" font-weight="800" fill="#173322">Farm topology in motion</text>')
    parts.append('<text x="34" y="54" font-size="11.5" fill="#607168">A compressed replay of the full 720-turn season · tiles + farmer + hired hands</text>')

    # phase rail
    phase_x=495; phase_y=35; phase_w=410
    phases=[(0,.17,'BUILD','#2A8A54'),(.17,.67,'SCALE','#168A9A'),(.67,.93,'PROTECT','#8B5FB2'),(.93,1.0,'CLOSE','#B78312')]
    for a,b,label,color in phases:
        x=phase_x+a*phase_w; w=(b-a)*phase_w
        parts.append(f'<rect x="{x:.1f}" y="{phase_y}" width="{w:.1f}" height="7" rx="3.5" fill="{color}" opacity=".72"/>')
        if w>45:
            parts.append(f'<text x="{x+w/2:.1f}" y="{phase_y+22}" text-anchor="middle" font-size="9" font-weight="800" fill="{color}">{label}</text>')
    parts.append(f'<circle cx="{phase_x}" cy="{phase_y+3.5}" r="6" fill="#FFFFFF" stroke="#173322" stroke-width="2"><animate attributeName="cx" values="{phase_x};{phase_x+phase_w}" dur="{duration}s" repeatCount="indefinite"/></circle>')

    # map background and grid
    parts.append(f'<rect x="{map_x-8}" y="{map_y-8}" width="{map_w+16}" height="{map_h+16}" rx="18" fill="#FFFFFF" stroke="#D6E2DA"/>')
    nframes=len(frames)
    for r in range(rows):
        for c in range(cols):
            vals=[colors[category(f['tiles'][r][c])] for f in farms]
            x=map_x+c*cell; y=map_y+r*cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="4" fill="{vals[0]}"><animate attributeName="fill" values="{";".join(vals)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # moving farmer
    fx=[]; fy=[]
    for farm in farms:
        rr,cc=farm['farmer']
        fx.append(map_x+cc*cell+(cell-gap)/2); fy.append(map_y+rr*cell+(cell-gap)/2)
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="8.8" fill="#FFFFFF" stroke="#173322" stroke-width="3"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="3.2" fill="#2A8A54"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')

    # hired hands
    max_hands=max(len(f['hands']) for f in farms)
    offsets=[(-5,-5),(5,-5),(-5,5),(5,5),(0,-7),(0,7),(-7,0),(7,0)]
    for h in range(max_hands):
        xs=[]; ys=[]; op=[]
        dx,dy=offsets[h%len(offsets)]
        for f in farms:
            if h < len(f['hands']):
                rr,cc=f['hands'][h]
                xs.append(map_x+cc*cell+(cell-gap)/2+dx*.55); ys.append(map_y+rr*cell+(cell-gap)/2+dy*.55); op.append('0.9')
            else:
                xs.append(map_x); ys.append(map_y); op.append('0')
        parts.append(f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.4" opacity="{op[0]}"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in xs)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in ys)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="opacity" values="{";".join(op)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></circle>')

    # right-side legend / readout
    sx=350
    parts.append(f'<text x="{sx}" y="88" font-size="11" font-weight="800" letter-spacing="1.3" fill="#607168">WHAT TO WATCH</text>')
    notes=[('Capacity expands','More cells become productive before the closeout.','#2A8A54'),('Labor circulates','White/teal markers reveal routing and service pressure.','#168A9A'),('Weeds are local shocks','Purple cells appear stochastically; repair should stay local.','#A66BB5'),('Deadline changes behavior','The final phase converts operating value back to cash.','#B78312')]
    yy=108
    for title,desc,col in notes:
        parts.append(f'<circle cx="{sx+4}" cy="{yy+3}" r="4" fill="{col}"/><text x="{sx+17}" y="{yy+6}" font-size="12.5" font-weight="800" fill="#173322">{html.escape(title)}</text><text x="{sx+17}" y="{yy+24}" font-size="10.5" fill="#607168">{html.escape(desc)}</text>')
        yy+=52

    # legend
    parts.append(f'<text x="{sx}" y="317" font-size="10" font-weight="800" letter-spacing="1.2" fill="#607168">TILES</text>')
    legend=[('Empty','EMPTY'),('Wheat','WHEAT'),('Strawberry','STRAWBERRY'),('Melon','MELON'),('Pasture','PASTURE'),('Weed','WEED'),('Locked','LOCKED')]
    lx=sx; ly=331
    for i,(label,key) in enumerate(legend):
        col=i%4; row=i//4; x=lx+col*112; y=ly+row*27
        parts.append(f'<rect x="{x}" y="{y-10}" width="13" height="13" rx="3" fill="{colors[key]}"/><text x="{x+19}" y="{y+1}" font-size="10" fill="#53695D">{label}</text>')
    parts.append(f'<circle cx="{sx+4}" cy="389" r="6" fill="#fff" stroke="#173322" stroke-width="2"/><text x="{sx+17}" y="393" font-size="10" fill="#53695D">Farmer</text><circle cx="{sx+99}" cy="389" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.3"/><text x="{sx+111}" y="393" font-size="10" fill="#53695D">Hands</text>')
    parts.append('</svg></div>')
    display(HTML(''.join(parts)))

demo_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 910001}, debug=False)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    demo_env.run([str(agent_path), str(agent_path)])
assert len(demo_env.steps) == 720
assert [str(s.status) for s in demo_env.steps[-1]] == ["DONE", "DONE"]
show_farm_motion(demo_env, seat=0, stride=10, duration=18)


from pathlib import Path
from collections import Counter
from cycler import cycler
import contextlib
import gzip
import html
import hashlib
import io
import math
import py_compile
import tarfile
import tempfile

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
from IPython.display import HTML, Image, display

# Silence only optional environment import chatter.
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

# Figures use a light, self-contained canvas so the saved outputs remain readable
# in both Kaggle light and dark themes.
FOREST = "#F7FAF8"
PANEL = "#FFFFFF"
GRID = "#D6E2DA"
TEXT = "#173322"
MUTED = "#607168"
PALETTE = ["#23864F", "#168A9A", "#B78312", "#8B5FB2", "#C75B4F", "#5577B8"]

plt.rcParams.update({
    "figure.dpi": 76,
    "savefig.dpi": 76,
    "font.size": 10,
    "figure.facecolor": FOREST,
    "axes.facecolor": PANEL,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": TEXT,
    "grid.color": GRID,
    "axes.prop_cycle": cycler(color=PALETTE),
})

def forest_axes(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.grid(alpha=.55)
    if title:
        ax.set_title(title, color=TEXT, fontsize=14, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT)
    return ax

def show_forest_figure(fig, quality=84):
    fig.patch.set_facecolor(FOREST)
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="jpeg",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pil_kwargs={"quality": quality, "optimize": True},
    )
    plt.close(fig)
    display(Image(data=buffer.getvalue(), format="jpeg"))

def show_forest_table(frame, caption=None, formats=None):
    """Theme-independent compact table for precise audit data."""
    table = frame.copy()
    if formats:
        for column, formatter in formats.items():
            if column in table:
                table[column] = table[column].map(formatter)
    caption_html = f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:0 0 9px">{caption}</div>' if caption else ""
    html = table.to_html(index=False, border=0, classes="forest-table", escape=False)
    style = ("<style>.forest-table{border-collapse:collapse;width:100%;color:#173322;font-size:13.5px}"
             ".forest-table th{background:#eef6f1;color:#274b38;text-align:left;padding:10px 11px;border-bottom:1px solid #cbded1;font-size:12px;letter-spacing:.02em}"
             ".forest-table td{padding:9px 11px;border-bottom:1px solid #e1ebe4;color:#294438}"
             ".forest-table tr:nth-child(even){background:#f8fbf9}.forest-table tr:nth-child(odd){background:#fff}"
             ".forest-table tbody tr:last-child td{border-bottom:0}</style>")
    wrapper = '<div style="background:#fff;border:1px solid #d3e1d8;border-radius:17px;padding:15px 16px;overflow-x:auto;box-shadow:0 5px 16px rgba(24,68,44,.05);color:#173322">'
    display(HTML(wrapper + caption_html + style + html + "</div>"))


def show_kpi_cards(items, eyebrow="Observed in this run"):
    cards = []
    for label, value, note, accent in items:
        cards.append(
            f'<div style="background:#fff;border:1px solid #d5e3da;border-top:4px solid {accent};border-radius:16px;padding:14px 15px;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
            f'<div style="font-size:10px;letter-spacing:.11em;text-transform:uppercase;font-weight:800;color:#64786c">{label}</div>'
            f'<div style="font-size:23px;font-weight:850;letter-spacing:-.02em;margin:3px 0 2px;color:#173322">{value}</div>'
            f'<div style="font-size:12px;color:#687970;line-height:1.35">{note}</div></div>'
        )
    display(HTML(
        f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:18px 0 8px">{eyebrow}</div>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:0 0 12px">' + ''.join(cards) + '</div>'
    ))


def show_insight(title, body, accent="#2a8a54", tag="INSIGHT"):
    display(HTML(
        f'<div style="background:#fff;border:1px solid #d5e3da;border-left:5px solid {accent};border-radius:15px;padding:14px 16px;margin:12px 0;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
        f'<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:{accent};margin-bottom:4px">{tag}</div>'
        f'<div style="font-weight:800;margin-bottom:4px;color:#173322">{title}</div>'
        f'<div style="color:#53695d;line-height:1.55;font-size:13.5px">{body}</div></div>'
    ))

def shade_season_phases(ax):
    """Light phase bands that connect diagnostics to the 30-day strategy atlas."""
    phases = [
        (1, 5, "BUILD", "#2A8A54"),
        (5, 20, "SCALE", "#168A9A"),
        (20, 28, "PROTECT", "#8B5FB2"),
        (28, 30, "CLOSE", "#B78312"),
    ]
    for start, end, label, color in phases:
        ax.axvspan(start, end, color=color, alpha=.055, lw=0, zorder=0)
        ax.text(
            (start + end) / 2,
            .965,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color=color,
            alpha=.82,
        )
    return ax


def show_market_motion(prices, item="STRAWBERRY", probe_quantity=20):
    """A tiny SVG animation: no GIF, no base64, and only a few KB of notebook output."""
    prices = np.asarray(prices, dtype=float)
    revenue = np.cumsum(prices)
    if len(prices) < 3:
        return

    width, height = 960, 370
    left = (62, 86, 360, 205)
    right = (540, 86, 360, 205)

    def path_for(values, box):
        x0, y0, w, h = box
        values = np.asarray(values, dtype=float)
        lo, hi = float(values.min()), float(values.max())
        span = max(hi - lo, 1.0)
        pts = []
        for i, value in enumerate(values):
            x = x0 + (w * i / max(len(values) - 1, 1))
            y = y0 + h - h * (float(value) - lo) / span
            pts.append((x, y))
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts), lo, hi

    price_path, p_lo, p_hi = path_for(prices, left)
    rev_path, r_lo, r_hi = path_for(revenue, right)
    q = min(int(probe_quantity), max(1, len(prices) // 3))
    impact_score = float(q * max(0, prices[0] - prices[min(q, len(prices)-1)]))

    def money(v):
        return f"${v:,.0f}"

    svg = f'''<div style="background:#fff;border:1px solid #d5e3da;border-radius:22px;padding:16px 16px 12px;box-shadow:0 8px 24px rgba(24,68,44,.06);margin:12px 0 16px;overflow-x:auto;color:#173322">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px">
      <div style="flex:1;min-width:145px;background:#f2faf5;border:1px solid #d8e8dd;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">OPENING QUOTE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[0])}</div></div>
      <div style="flex:1;min-width:145px;background:#eef8fa;border:1px solid #d5e6e9;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">AFTER {len(prices)} UNITS</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[-1])}</div></div>
      <div style="flex:1;min-width:145px;background:#f8f1fb;border:1px solid #e5d9ec;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">{q}-UNIT IMPACT SCORE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(impact_score)}</div></div>
      <div style="flex:1;min-width:145px;background:#fff8e9;border:1px solid #eee0bf;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">TOTAL REVENUE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(revenue[-1])}</div></div>
    </div>
    <svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:980px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-label="Animated market price erosion and cumulative revenue">
      <defs>
        <linearGradient id="kgPriceGrad" x1="0" x2="1"><stop offset="0" stop-color="#23864F"/><stop offset="1" stop-color="#168A9A"/></linearGradient>
        <linearGradient id="kgRevGrad" x1="0" x2="1"><stop offset="0" stop-color="#168A9A"/><stop offset="1" stop-color="#8B5FB2"/></linearGradient>
        <filter id="kgGlow"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect x="18" y="14" width="924" height="334" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>
      <text x="62" y="48" fill="#173322" font-size="17" font-weight="800">Market pressure in motion · {item.title()}</text>
      <text x="62" y="68" fill="#607168" font-size="12">The same sale becomes less valuable as shared inventory moves before it.</text>

      <rect x="44" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <rect x="522" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <text x="62" y="105" fill="#173322" font-size="13" font-weight="800">SELL PRICE</text>
      <text x="540" y="105" fill="#173322" font-size="13" font-weight="800">CUMULATIVE REVENUE</text>
      <text x="62" y="299" fill="#607168" font-size="11">units added to shared market inventory →</text>
      <text x="540" y="299" fill="#607168" font-size="11">units sold →</text>
      <text x="404" y="126" text-anchor="end" fill="#607168" font-size="10">{money(p_hi)}</text>
      <text x="404" y="282" text-anchor="end" fill="#607168" font-size="10">{money(p_lo)}</text>
      <text x="882" y="126" text-anchor="end" fill="#607168" font-size="10">{money(r_hi)}</text>
      <text x="882" y="282" text-anchor="end" fill="#607168" font-size="10">{money(r_lo)}</text>

      <path d="{price_path}" fill="none" stroke="#BFD6C8" stroke-width="4" opacity=".5"/>
      <path id="kgPricePath" d="{price_path}" pathLength="1" fill="none" stroke="url(#kgPriceGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#23864F" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgPricePath"/></animateMotion>
      </circle>

      <path d="{rev_path}" fill="none" stroke="#C9D9E1" stroke-width="4" opacity=".5"/>
      <path id="kgRevPath" d="{rev_path}" pathLength="1" fill="none" stroke="url(#kgRevGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#8B5FB2" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgRevPath"/></animateMotion>
      </circle>

      <text x="480" y="338" text-anchor="middle" fill="#53695D" font-size="12">SVG animation: lightweight, vector-sharp, and free of embedded GIF/base64 payloads.</text>
    </svg></div>'''
    display(HTML(svg))



def show_farm_motion(env, seat=0, stride=6, duration=18):
    frames = list(range(0, len(env.steps), stride))
    if frames[-1] != len(env.steps)-1:
        frames.append(len(env.steps)-1)
    observations = [env.steps[idx][seat].observation for idx in frames]
    player_id = int(observations[0].player)
    farms = [obs.farms[player_id] for obs in observations]
    rows, cols = len(farms[0]['tiles']), len(farms[0]['tiles'][0])

    colors = {
        'LOCKED':'#20362C','EMPTY':'#E6EEE9','WHEAT':'#E5B94E','CARROT':'#E69A4A','TOMATO':'#D65A4A',
        'STRAWBERRY':'#D85C70','MELON':'#61B873','PASTURE':'#4B9DA5','WEED':'#A66BB5','OTHER':'#A9B8AF'
    }
    def category(tile):
        if tile == 'LOCKED': return 'LOCKED'
        if tile is None: return 'EMPTY'
        if isinstance(tile, dict):
            kind = tile.get('kind')
            if kind == 'PLANT': return tile.get('crop','OTHER')
            if kind == 'PASTURE': return 'PASTURE'
            if kind == 'WEED': return 'WEED'
        return 'OTHER'

    cell=27; gap=2; map_x=34; map_y=74
    map_w=cols*cell; map_h=rows*cell
    width=960; height=405
    parts=[]
    parts.append(f'<div style="background:#fff;border:1px solid #d5e3da;border-radius:24px;padding:14px 14px 10px;box-shadow:0 10px 28px rgba(24,68,44,.07);margin:14px 0 16px;overflow-x:auto;color:#173322">')
    parts.append(f'<svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:1040px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg">')
    parts.append('<rect x="8" y="8" width="944" height="389" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>')
    parts.append('<text x="34" y="34" font-size="17" font-weight="800" fill="#173322">Farm topology in motion</text>')
    parts.append('<text x="34" y="54" font-size="11.5" fill="#607168">A compressed replay of the full 720-turn season · tiles + farmer + hired hands</text>')

    # phase rail
    phase_x=495; phase_y=35; phase_w=410
    phases=[(0,.17,'BUILD','#2A8A54'),(.17,.67,'SCALE','#168A9A'),(.67,.93,'PROTECT','#8B5FB2'),(.93,1.0,'CLOSE','#B78312')]
    for a,b,label,color in phases:
        x=phase_x+a*phase_w; w=(b-a)*phase_w
        parts.append(f'<rect x="{x:.1f}" y="{phase_y}" width="{w:.1f}" height="7" rx="3.5" fill="{color}" opacity=".72"/>')
        if w>45:
            parts.append(f'<text x="{x+w/2:.1f}" y="{phase_y+22}" text-anchor="middle" font-size="9" font-weight="800" fill="{color}">{label}</text>')
    parts.append(f'<circle cx="{phase_x}" cy="{phase_y+3.5}" r="6" fill="#FFFFFF" stroke="#173322" stroke-width="2"><animate attributeName="cx" values="{phase_x};{phase_x+phase_w}" dur="{duration}s" repeatCount="indefinite"/></circle>')

    # map background and grid
    parts.append(f'<rect x="{map_x-8}" y="{map_y-8}" width="{map_w+16}" height="{map_h+16}" rx="18" fill="#FFFFFF" stroke="#D6E2DA"/>')
    nframes=len(frames)
    for r in range(rows):
        for c in range(cols):
            vals=[colors[category(f['tiles'][r][c])] for f in farms]
            x=map_x+c*cell; y=map_y+r*cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="4" fill="{vals[0]}"><animate attributeName="fill" values="{";".join(vals)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # moving farmer
    fx=[]; fy=[]
    for farm in farms:
        rr,cc=farm['farmer']
        fx.append(map_x+cc*cell+(cell-gap)/2); fy.append(map_y+rr*cell+(cell-gap)/2)
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="8.8" fill="#FFFFFF" stroke="#173322" stroke-width="3"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="3.2" fill="#2A8A54"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')

    # hired hands
    max_hands=max(len(f['hands']) for f in farms)
    offsets=[(-5,-5),(5,-5),(-5,5),(5,5),(0,-7),(0,7),(-7,0),(7,0)]
    for h in range(max_hands):
        xs=[]; ys=[]; op=[]
        dx,dy=offsets[h%len(offsets)]
        for f in farms:
            if h < len(f['hands']):
                rr,cc=f['hands'][h]
                xs.append(map_x+cc*cell+(cell-gap)/2+dx*.55); ys.append(map_y+rr*cell+(cell-gap)/2+dy*.55); op.append('0.9')
            else:
                xs.append(map_x); ys.append(map_y); op.append('0')
        parts.append(f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.4" opacity="{op[0]}"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in xs)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in ys)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="opacity" values="{";".join(op)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></circle>')

    # right-side legend / readout
    sx=350
    parts.append(f'<text x="{sx}" y="88" font-size="11" font-weight="800" letter-spacing="1.3" fill="#607168">WHAT TO WATCH</text>')
    notes=[('Capacity expands','More cells become productive before the closeout.','#2A8A54'),('Labor circulates','White/teal markers reveal routing and service pressure.','#168A9A'),('Weeds are local shocks','Purple cells appear stochastically; repair should stay local.','#A66BB5'),('Deadline changes behavior','The final phase converts operating value back to cash.','#B78312')]
    yy=108
    for title,desc,col in notes:
        parts.append(f'<circle cx="{sx+4}" cy="{yy+3}" r="4" fill="{col}"/><text x="{sx+17}" y="{yy+6}" font-size="12.5" font-weight="800" fill="#173322">{html.escape(title)}</text><text x="{sx+17}" y="{yy+24}" font-size="10.5" fill="#607168">{html.escape(desc)}</text>')
        yy+=52

    # legend
    parts.append(f'<text x="{sx}" y="317" font-size="10" font-weight="800" letter-spacing="1.2" fill="#607168">TILES</text>')
    legend=[('Empty','EMPTY'),('Wheat','WHEAT'),('Strawberry','STRAWBERRY'),('Melon','MELON'),('Pasture','PASTURE'),('Weed','WEED'),('Locked','LOCKED')]
    lx=sx; ly=331
    for i,(label,key) in enumerate(legend):
        col=i%4; row=i//4; x=lx+col*112; y=ly+row*27
        parts.append(f'<rect x="{x}" y="{y-10}" width="13" height="13" rx="3" fill="{colors[key]}"/><text x="{x+19}" y="{y+1}" font-size="10" fill="#53695D">{label}</text>')
    parts.append(f'<circle cx="{sx+4}" cy="389" r="6" fill="#fff" stroke="#173322" stroke-width="2"/><text x="{sx+17}" y="393" font-size="10" fill="#53695D">Farmer</text><circle cx="{sx+99}" cy="389" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.3"/><text x="{sx+111}" y="393" font-size="10" fill="#53695D">Hands</text>')
    parts.append('</svg></div>')
    display(HTML(''.join(parts)))





opening = demo_env.steps[0][0].observation
switch_obs = demo_env.steps[168][0].observation
switch_shops = tuple(str(x) for x in (switch_obs.town.get("unlocked_shops", []) or []))

def route_from_shops(shops):
    shops = tuple(shops)
    ice_then_yarn = len(shops) >= 2 and shops[0] == "ICE_CREAM_SHOP" and shops[1] == "YARN_STORE"
    return "High-capacity" if "YARN_STORE" in shops and not ice_then_yarn else "Balanced"

first_seen = {}
for step, states in enumerate(demo_env.steps):
    shops = states[0].observation.town.get("unlocked_shops", []) or []
    for shop in shops:
        first_seen.setdefault(str(shop), step)

signal = pd.DataFrame(
    [(shop, step, step // 24 + 1, step % 24) for shop, step in first_seen.items()],
    columns=["shop", "first turn", "day", "hour"],
).sort_values("first turn")
show_forest_table(signal, "Public town signals observed in the live replay")
show_kpi_cards([
    ("Decision turn", "168", "after a shared prefix", "#168a9a"),
    ("Visible shops", str(len(switch_shops)), "at the checkpoint", "#2a8a54"),
    ("Selected route", route_from_shops(switch_shops), "for this replay", "#8b5fb2"),
], eyebrow="Opening signal")
show_insight(
    "A small signal can justify a large structural choice",
    "The controller waits until the two candidate economies have followed the same opening. Only then does it use the public shop sequence to choose the production route, which keeps the decision interpretable and limits overreaction to noisy short-term prices.",
    accent="#168a9a", tag="SIGNAL DESIGN"
)

AGENT_FILES = {"main.py": AGENT_SOURCE}
AGENT_DIR = Path("kaggriculture_agent").resolve()
AGENT_DIR.mkdir(exist_ok=True)
for name, source in AGENT_FILES.items():
    (AGENT_DIR / name).write_text(source, encoding="utf-8")
agent_path = (AGENT_DIR / "main.py").resolve()
print(f"Materialized {len(AGENT_FILES)} submission file")

import py_compile
source_bytes = {name: (AGENT_DIR / name).read_bytes() for name in AGENT_FILES}
for name in AGENT_FILES:
    py_compile.compile(str(AGENT_DIR / name), doraise=True)
assert source_bytes["main.py"] == AGENT_SOURCE.encode()
assert hashlib.sha256(source_bytes["main.py"]).hexdigest() == EXPECTED_AGENT_SHA

spec = importlib.util.spec_from_file_location("public_submission_agent", agent_path)
public_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public_agent)
assert callable(public_agent.agent)

source_check = pd.DataFrame([{
    "files": len(AGENT_FILES),
    "syntax": "PASS",
    "entrypoint": "agent",
    "source bytes": len(source_bytes["main.py"]),
    "sha256": EXPECTED_AGENT_SHA[:16] + "…",
}])
show_forest_table(source_check, "Exact submission source check")

audit_rows = []
for step in [0, 72, 120, 167, 168, 169]:
    obs = demo_env.steps[step][0].observation
    shops = tuple(str(x) for x in (obs.town.get("unlocked_shops", []) or []))
    audit_rows.append({
        "turn": step,
        "day": step // 24 + 1,
        "shops": " → ".join(shops) if shops else "—",
        "route if committed now": route_from_shops(shops),
        "decision active": "YES" if step >= 168 else "NO",
    })
selector_audit = pd.DataFrame(audit_rows)
show_forest_table(selector_audit, "Public-state selector audit")

VALIDATION_SEED = 910019

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": VALIDATION_SEED}, debug=False)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    env.run([str(agent_path), str(agent_path)])
final = env.steps[-1]
public_farms = final[0].observation.farms

def count_active_actions(steps, seat):
    active = 0
    market_orders = 0
    for states in steps:
        action = states[seat].action or {}
        units = [action.get("farmer")] + list(action.get("hands", []) or [])
        active += sum(1 for item in units if item and item[0] != "PASS")
        market_orders += len(action.get("market", []) or [])
    return active, market_orders

rows = []
for seat in (0, 1):
    player_id = int(final[seat].observation.player)
    active_actions, market_orders = count_active_actions(env.steps, seat)
    rows.append({
        "seed": VALIDATION_SEED,
        "seat": seat,
        "turns": len(env.steps),
        "status": str(final[seat].status),
        "terminal_bank": float(public_farms[player_id]["money"]),
        "final_reward": float(final[seat].reward),
        "active_farm_actions": active_actions,
        "market_orders": market_orders,
        "runtime_check": "PASS",
    })
validation = pd.DataFrame(rows)
assert len(env.steps) == 720
assert validation["status"].eq("DONE").all()
assert validation["terminal_bank"].map(math.isfinite).all()
assert validation["final_reward"].map(math.isfinite).all()
assert (validation["active_farm_actions"] > 0).all()
assert (validation["market_orders"] > 0).all()
assert np.allclose(validation["terminal_bank"], validation["final_reward"])

show_kpi_cards([
    ("Episode", f"{len(env.steps)} turns", "complete season", "#168a9a"),
    ("Runtime", "DONE × 2", "both seats finished", "#2a8a54"),
    ("Farm work", f"{int(validation['active_farm_actions'].sum()):,}", "non-pass unit actions", "#b78312"),
    ("Market", f"{int(validation['market_orders'].sum()):,}", "orders issued", "#8b5fb2"),
], eyebrow="Full-season validation")
show_forest_table(validation, "Full-season runtime card", formats={
    "terminal_bank": lambda x: f"{x:,.0f}",
    "final_reward": lambda x: f"{x:,.0f}",
    "active_farm_actions": lambda x: f"{x:,}",
    "market_orders": lambda x: f"{x:,}",
})

# Compact traces reused by the diagnostics below.
days = list(range(1, 31))
daily_bank = {0: [], 1: []}
daily_prices = {name: [] for name in ["MELON", "STRAWBERRY", "MILK", "WOOL", "WHEAT"]}
daily_assets = {"Hands": [], "Plants": [], "Animals": [], "Shed units": []}
for day in range(30):
    step = min((day + 1) * 24 - 1, len(env.steps) - 1)
    states = env.steps[step]
    canonical = states[0].observation
    for seat in (0, 1):
        daily_bank[seat].append(float(canonical.farms[seat]["money"]))
    for product in daily_prices:
        daily_prices[product].append(float(canonical.market["prices"][product]))
    farm = canonical.farms[0]
    private = states[0].observation.private
    tiles = farm.get("tiles", [])
    daily_assets["Hands"].append(len(farm.get("hands", [])))
    daily_assets["Plants"].append(sum(1 for row in tiles for tile in row if isinstance(tile, dict) and tile.get("kind") == "PLANT"))
    daily_assets["Animals"].append(sum(1 for row in tiles for tile in row if isinstance(tile, dict) and tile.get("kind") in {"COOP", "PASTURE"} and tile.get("animal")))
    daily_assets["Shed units"].append(sum(private.get("shed", {}).values()))

bank0 = np.asarray(daily_bank[0], dtype=float)
bank1 = np.asarray(daily_bank[1], dtype=float)
fig, ax = plt.subplots(figsize=(9.4, 4.1))
ax.plot(days, bank0, linewidth=2.6, marker="o", markersize=3.0, label="Seat 0")
if not np.allclose(bank0, bank1, rtol=0.0, atol=1e-9):
    ax.plot(days, bank1, linewidth=1.8, alpha=.75, label="Seat 1")
    ax.legend(frameon=False, labelcolor=TEXT)
forest_axes(ax, "Bank balance through the 30-day capital cycle", "Day", "Bank balance")
shade_season_phases(ax)
ax.grid(axis="y", alpha=.22)
show_forest_figure(fig)

fig, ax = plt.subplots(figsize=(9.4, 4.2))
for product, values in daily_prices.items():
    ax.plot(days, values, linewidth=1.9, label=product.title())
forest_axes(ax, "Shared-market quotes remain non-stationary", "Day", "Market price")
shade_season_phases(ax)
ax.legend(frameon=False, labelcolor=TEXT, ncol=5, fontsize=8.5)
show_forest_figure(fig)

fig, ax = plt.subplots(figsize=(9.4, 4.0))
for label, values in daily_assets.items():
    ax.plot(days, values, linewidth=2.0, label=label)
forest_axes(ax, "Operating capacity grows before final liquidation", "Day", "Count / units")
shade_season_phases(ax)
ax.legend(frameon=False, labelcolor=TEXT, ncol=4, fontsize=9)
show_forest_figure(fig)

movement_ops = {"NORTH", "SOUTH", "EAST", "WEST"}
crop_ops = {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}
livestock_ops = {"FEED", "CARE", "COLLECT_FERTILIZER"}
logistics_ops = {"PICKUP", "DROP", "PLACE", "BUILD_PASTURE"}

mix = Counter()
for states in env.steps:
    action = states[0].action or {}
    for unit_action in [action.get("farmer")] + list(action.get("hands", []) or []):
        if not unit_action:
            continue
        op = unit_action[0]
        if op in movement_ops: mix["Movement"] += 1
        elif op in crop_ops: mix["Crop work"] += 1
        elif op in livestock_ops: mix["Livestock"] += 1
        elif op in logistics_ops: mix["Logistics"] += 1
        elif op == "PASS": mix["Pass"] += 1
        else: mix["Other farm"] += 1
    for order in action.get("market", []) or []:
        if order:
            mix["Market sales" if order[0] == "SELL" else "Investment / buying"] += 1

mix_frame = pd.DataFrame(mix.items(), columns=["category", "actions"]).sort_values("actions")
fig, ax = plt.subplots(figsize=(9.4, 4.2))
ax.barh(mix_frame["category"], mix_frame["actions"], color=PALETTE[1], alpha=.88)
forest_axes(ax, "What the selected route spends 720 turns doing", "Action count", "")
ax.grid(axis="x", alpha=.25); ax.grid(axis="y", alpha=0)
for i, value in enumerate(mix_frame["actions"]):
    ax.text(value + max(mix_frame["actions"])*.012, i, f"{value:,}", va="center", color=TEXT, fontsize=9)
show_forest_figure(fig)

min_bank_day = int(np.argmin(daily_bank[0])) + 1
peak_hands = int(max(daily_assets["Hands"]))
peak_plants = int(max(daily_assets["Plants"]))
show_kpi_cards([
    ("Capital trough", f"Day {min_bank_day}", f"bank {min(daily_bank[0]):,.0f}", "#b78312"),
    ("Peak hands", f"{peak_hands}", "labor capacity", "#168a9a"),
    ("Peak plants", f"{peak_plants}", "crop footprint", "#2a8a54"),
    ("Observed actions", f"{int(sum(mix.values())):,}", "farm + market events", "#8b5fb2"),
], eyebrow="Trace readout")

import gzip, tarfile, tempfile
archive_path = Path("submission.tar.gz")
main_bytes = source_bytes["main.py"]
with archive_path.open("wb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as archive:
            info = tarfile.TarInfo("main.py")
            info.size = len(main_bytes)
            info.mode = 0o644
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(main_bytes))

with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getnames()
    archived_main = archive.extractfile("main.py").read()
assert members == ["main.py"]
assert archived_main == main_bytes
archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()

extract_dir = Path("submission_extract").resolve()
if extract_dir.exists():
    shutil.rmtree(extract_dir)
extract_dir.mkdir()
(extract_dir / "main.py").write_bytes(archived_main)
py_compile.compile(str(extract_dir / "main.py"), doraise=True)

archive_env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 910021}, debug=False)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    archive_env.run([str(extract_dir / "main.py"), str(extract_dir / "main.py")])
archive_statuses = [str(state.status) for state in archive_env.steps[-1]]
archive_rewards = [float(state.reward) for state in archive_env.steps[-1]]
assert len(archive_env.steps) == 720
assert archive_statuses == ["DONE", "DONE"]
assert all(math.isfinite(v) for v in archive_rewards)

archive_check = pd.DataFrame([{
    "files": len(members),
    "source bytes": "MATCH",
    "syntax": "PASS",
    "archive rerun": "PASS",
    "turns": len(archive_env.steps),
    "status": " / ".join(archive_statuses),
    "sha256": archive_sha[:16] + "…",
}])
show_forest_table(archive_check, "Submission archive verification")
print(f"Archive ready: {archive_path} ({archive_path.stat().st_size:,} bytes)")
