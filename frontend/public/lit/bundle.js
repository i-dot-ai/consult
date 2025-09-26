/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1 = globalThis,
  e$2 =
    t$1.ShadowRoot &&
    (void 0 === t$1.ShadyCSS || t$1.ShadyCSS.nativeShadow) &&
    "adoptedStyleSheets" in Document.prototype &&
    "replace" in CSSStyleSheet.prototype,
  s$1 = Symbol(),
  o$2 = new WeakMap();
let n$2 = class n {
  constructor(t, e, o) {
    if (((this._$cssResult$ = true), o !== s$1))
      throw Error(
        "CSSResult is not constructable. Use `unsafeCSS` or `css` instead.",
      );
    ((this.cssText = t), (this.t = e));
  }
  get styleSheet() {
    let t = this.o;
    const s = this.t;
    if (e$2 && void 0 === t) {
      const e = void 0 !== s && 1 === s.length;
      (e && (t = o$2.get(s)),
        void 0 === t &&
          ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText),
          e && o$2.set(s, t)));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const r$3 = (t) => new n$2("string" == typeof t ? t : t + "", void 0, s$1),
  i$3 = (t, ...e) => {
    const o =
      1 === t.length
        ? t[0]
        : e.reduce(
            (e, s, o) =>
              e +
              ((t) => {
                if (true === t._$cssResult$) return t.cssText;
                if ("number" == typeof t) return t;
                throw Error(
                  "Value passed to 'css' function must be a 'css' function result: " +
                    t +
                    ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.",
                );
              })(s) +
              t[o + 1],
            t[0],
          );
    return new n$2(o, t, s$1);
  },
  S$1 = (s, o) => {
    if (e$2)
      s.adoptedStyleSheets = o.map((t) =>
        t instanceof CSSStyleSheet ? t : t.styleSheet,
      );
    else
      for (const e of o) {
        const o = document.createElement("style"),
          n = t$1.litNonce;
        (void 0 !== n && o.setAttribute("nonce", n),
          (o.textContent = e.cssText),
          s.appendChild(o));
      }
  },
  c$2 = e$2
    ? (t) => t
    : (t) =>
        t instanceof CSSStyleSheet
          ? ((t) => {
              let e = "";
              for (const s of t.cssRules) e += s.cssText;
              return r$3(e);
            })(t)
          : t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */ const {
    is: i$2,
    defineProperty: e$1,
    getOwnPropertyDescriptor: r$2,
    getOwnPropertyNames: h$1,
    getOwnPropertySymbols: o$1,
    getPrototypeOf: n$1,
  } = Object,
  a$1 = globalThis,
  c$1 = a$1.trustedTypes,
  l$1 = c$1 ? c$1.emptyScript : "",
  p$1 = a$1.reactiveElementPolyfillSupport,
  d$1 = (t, s) => t,
  u$1 = {
    toAttribute(t, s) {
      switch (s) {
        case Boolean:
          t = t ? l$1 : null;
          break;
        case Object:
        case Array:
          t = null == t ? t : JSON.stringify(t);
      }
      return t;
    },
    fromAttribute(t, s) {
      let i = t;
      switch (s) {
        case Boolean:
          i = null !== t;
          break;
        case Number:
          i = null === t ? null : Number(t);
          break;
        case Object:
        case Array:
          try {
            i = JSON.parse(t);
          } catch (t) {
            i = null;
          }
      }
      return i;
    },
  },
  f$1 = (t, s) => !i$2(t, s),
  y$1 = {
    attribute: true,
    type: String,
    converter: u$1,
    reflect: false,
    hasChanged: f$1,
  };
((Symbol.metadata ??= Symbol("metadata")),
  (a$1.litPropertyMetadata ??= new WeakMap()));
class b extends HTMLElement {
  static addInitializer(t) {
    (this._$Ei(), (this.l ??= []).push(t));
  }
  static get observedAttributes() {
    return (this.finalize(), this._$Eh && [...this._$Eh.keys()]);
  }
  static createProperty(t, s = y$1) {
    if (
      (s.state && (s.attribute = false),
      this._$Ei(),
      this.elementProperties.set(t, s),
      !s.noAccessor)
    ) {
      const i = Symbol(),
        r = this.getPropertyDescriptor(t, i, s);
      void 0 !== r && e$1(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, s, i) {
    const { get: e, set: h } = r$2(this.prototype, t) ?? {
      get() {
        return this[s];
      },
      set(t) {
        this[s] = t;
      },
    };
    return {
      get() {
        return e?.call(this);
      },
      set(s) {
        const r = e?.call(this);
        (h.call(this, s), this.requestUpdate(t, r, i));
      },
      configurable: true,
      enumerable: true,
    };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? y$1;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d$1("elementProperties"))) return;
    const t = n$1(this);
    (t.finalize(),
      void 0 !== t.l && (this.l = [...t.l]),
      (this.elementProperties = new Map(t.elementProperties)));
  }
  static finalize() {
    if (this.hasOwnProperty(d$1("finalized"))) return;
    if (
      ((this.finalized = true),
      this._$Ei(),
      this.hasOwnProperty(d$1("properties")))
    ) {
      const t = this.properties,
        s = [...h$1(t), ...o$1(t)];
      for (const i of s) this.createProperty(i, t[i]);
    }
    const t = this[Symbol.metadata];
    if (null !== t) {
      const s = litPropertyMetadata.get(t);
      if (void 0 !== s)
        for (const [t, i] of s) this.elementProperties.set(t, i);
    }
    this._$Eh = new Map();
    for (const [t, s] of this.elementProperties) {
      const i = this._$Eu(t, s);
      void 0 !== i && this._$Eh.set(i, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s) {
    const i = [];
    if (Array.isArray(s)) {
      const e = new Set(s.flat(1 / 0).reverse());
      for (const s of e) i.unshift(c$2(s));
    } else void 0 !== s && i.push(c$2(s));
    return i;
  }
  static _$Eu(t, s) {
    const i = s.attribute;
    return false === i
      ? void 0
      : "string" == typeof i
        ? i
        : "string" == typeof t
          ? t.toLowerCase()
          : void 0;
  }
  constructor() {
    (super(),
      (this._$Ep = void 0),
      (this.isUpdatePending = false),
      (this.hasUpdated = false),
      (this._$Em = null),
      this._$Ev());
  }
  _$Ev() {
    ((this._$ES = new Promise((t) => (this.enableUpdating = t))),
      (this._$AL = new Map()),
      this._$E_(),
      this.requestUpdate(),
      this.constructor.l?.forEach((t) => t(this)));
  }
  addController(t) {
    ((this._$EO ??= new Set()).add(t),
      void 0 !== this.renderRoot && this.isConnected && t.hostConnected?.());
  }
  removeController(t) {
    this._$EO?.delete(t);
  }
  _$E_() {
    const t = new Map(),
      s = this.constructor.elementProperties;
    for (const i of s.keys())
      this.hasOwnProperty(i) && (t.set(i, this[i]), delete this[i]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t =
      this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return (S$1(t, this.constructor.elementStyles), t);
  }
  connectedCallback() {
    ((this.renderRoot ??= this.createRenderRoot()),
      this.enableUpdating(true),
      this._$EO?.forEach((t) => t.hostConnected?.()));
  }
  enableUpdating(t) {}
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, s, i) {
    this._$AK(t, i);
  }
  _$EC(t, s) {
    const i = this.constructor.elementProperties.get(t),
      e = this.constructor._$Eu(t, i);
    if (void 0 !== e && true === i.reflect) {
      const r = (
        void 0 !== i.converter?.toAttribute ? i.converter : u$1
      ).toAttribute(s, i.type);
      ((this._$Em = t),
        null == r ? this.removeAttribute(e) : this.setAttribute(e, r),
        (this._$Em = null));
    }
  }
  _$AK(t, s) {
    const i = this.constructor,
      e = i._$Eh.get(t);
    if (void 0 !== e && this._$Em !== e) {
      const t = i.getPropertyOptions(e),
        r =
          "function" == typeof t.converter
            ? { fromAttribute: t.converter }
            : void 0 !== t.converter?.fromAttribute
              ? t.converter
              : u$1;
      ((this._$Em = e),
        (this[e] = r.fromAttribute(s, t.type)),
        (this._$Em = null));
    }
  }
  requestUpdate(t, s, i) {
    if (void 0 !== t) {
      if (
        ((i ??= this.constructor.getPropertyOptions(t)),
        !(i.hasChanged ?? f$1)(this[t], s))
      )
        return;
      this.P(t, s, i);
    }
    false === this.isUpdatePending && (this._$ES = this._$ET());
  }
  P(t, s, i) {
    (this._$AL.has(t) || this._$AL.set(t, s),
      true === i.reflect &&
        this._$Em !== t &&
        (this._$Ej ??= new Set()).add(t));
  }
  async _$ET() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const t = this.scheduleUpdate();
    return (null != t && (await t), !this.isUpdatePending);
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (((this.renderRoot ??= this.createRenderRoot()), this._$Ep)) {
        for (const [t, s] of this._$Ep) this[t] = s;
        this._$Ep = void 0;
      }
      const t = this.constructor.elementProperties;
      if (t.size > 0)
        for (const [s, i] of t)
          true !== i.wrapped ||
            this._$AL.has(s) ||
            void 0 === this[s] ||
            this.P(s, this[s], i);
    }
    let t = false;
    const s = this._$AL;
    try {
      ((t = this.shouldUpdate(s)),
        t
          ? (this.willUpdate(s),
            this._$EO?.forEach((t) => t.hostUpdate?.()),
            this.update(s))
          : this._$EU());
    } catch (s) {
      throw ((t = false), this._$EU(), s);
    }
    t && this._$AE(s);
  }
  willUpdate(t) {}
  _$AE(t) {
    (this._$EO?.forEach((t) => t.hostUpdated?.()),
      this.hasUpdated || ((this.hasUpdated = true), this.firstUpdated(t)),
      this.updated(t));
  }
  _$EU() {
    ((this._$AL = new Map()), (this.isUpdatePending = false));
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t) {
    return true;
  }
  update(t) {
    ((this._$Ej &&= this._$Ej.forEach((t) => this._$EC(t, this[t]))),
      this._$EU());
  }
  updated(t) {}
  firstUpdated(t) {}
}
((b.elementStyles = []),
  (b.shadowRootOptions = { mode: "open" }),
  (b[d$1("elementProperties")] = new Map()),
  (b[d$1("finalized")] = new Map()),
  p$1?.({ ReactiveElement: b }),
  (a$1.reactiveElementVersions ??= []).push("2.0.4"));

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t = globalThis,
  i$1 = t.trustedTypes,
  s = i$1 ? i$1.createPolicy("lit-html", { createHTML: (t) => t }) : void 0,
  e = "$lit$",
  h = `lit$${Math.random().toFixed(9).slice(2)}$`,
  o = "?" + h,
  n = `<${o}>`,
  r$1 = document,
  l = () => r$1.createComment(""),
  c = (t) => null === t || ("object" != typeof t && "function" != typeof t),
  a = Array.isArray,
  u = (t) => a(t) || "function" == typeof t?.[Symbol.iterator],
  d = "[ \t\n\f\r]",
  f = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,
  v = /-->/g,
  _ = />/g,
  m = RegExp(
    `>|${d}(?:([^\\s"'>=/]+)(${d}*=${d}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,
    "g",
  ),
  p = /'/g,
  g = /"/g,
  $ = /^(?:script|style|textarea|title)$/i,
  y =
    (t) =>
    (i, ...s) => ({ _$litType$: t, strings: i, values: s }),
  x = y(1),
  T = Symbol.for("lit-noChange"),
  E = Symbol.for("lit-nothing"),
  A = new WeakMap(),
  C = r$1.createTreeWalker(r$1, 129);
function P(t, i) {
  if (!a(t) || !t.hasOwnProperty("raw"))
    throw Error("invalid template strings array");
  return void 0 !== s ? s.createHTML(i) : i;
}
const V = (t, i) => {
  const s = t.length - 1,
    o = [];
  let r,
    l = 2 === i ? "<svg>" : 3 === i ? "<math>" : "",
    c = f;
  for (let i = 0; i < s; i++) {
    const s = t[i];
    let a,
      u,
      d = -1,
      y = 0;
    for (; y < s.length && ((c.lastIndex = y), (u = c.exec(s)), null !== u); )
      ((y = c.lastIndex),
        c === f
          ? "!--" === u[1]
            ? (c = v)
            : void 0 !== u[1]
              ? (c = _)
              : void 0 !== u[2]
                ? ($.test(u[2]) && (r = RegExp("</" + u[2], "g")), (c = m))
                : void 0 !== u[3] && (c = m)
          : c === m
            ? ">" === u[0]
              ? ((c = r ?? f), (d = -1))
              : void 0 === u[1]
                ? (d = -2)
                : ((d = c.lastIndex - u[2].length),
                  (a = u[1]),
                  (c = void 0 === u[3] ? m : '"' === u[3] ? g : p))
            : c === g || c === p
              ? (c = m)
              : c === v || c === _
                ? (c = f)
                : ((c = m), (r = void 0)));
    const x = c === m && t[i + 1].startsWith("/>") ? " " : "";
    l +=
      c === f
        ? s + n
        : d >= 0
          ? (o.push(a), s.slice(0, d) + e + s.slice(d) + h + x)
          : s + h + (-2 === d ? i : x);
  }
  return [
    P(t, l + (t[s] || "<?>") + (2 === i ? "</svg>" : 3 === i ? "</math>" : "")),
    o,
  ];
};
class N {
  constructor({ strings: t, _$litType$: s }, n) {
    let r;
    this.parts = [];
    let c = 0,
      a = 0;
    const u = t.length - 1,
      d = this.parts,
      [f, v] = V(t, s);
    if (
      ((this.el = N.createElement(f, n)),
      (C.currentNode = this.el.content),
      2 === s || 3 === s)
    ) {
      const t = this.el.content.firstChild;
      t.replaceWith(...t.childNodes);
    }
    for (; null !== (r = C.nextNode()) && d.length < u; ) {
      if (1 === r.nodeType) {
        if (r.hasAttributes())
          for (const t of r.getAttributeNames())
            if (t.endsWith(e)) {
              const i = v[a++],
                s = r.getAttribute(t).split(h),
                e = /([.?@])?(.*)/.exec(i);
              (d.push({
                type: 1,
                index: c,
                name: e[2],
                strings: s,
                ctor:
                  "." === e[1] ? H : "?" === e[1] ? I : "@" === e[1] ? L : k,
              }),
                r.removeAttribute(t));
            } else
              t.startsWith(h) &&
                (d.push({ type: 6, index: c }), r.removeAttribute(t));
        if ($.test(r.tagName)) {
          const t = r.textContent.split(h),
            s = t.length - 1;
          if (s > 0) {
            r.textContent = i$1 ? i$1.emptyScript : "";
            for (let i = 0; i < s; i++)
              (r.append(t[i], l()),
                C.nextNode(),
                d.push({ type: 2, index: ++c }));
            r.append(t[s], l());
          }
        }
      } else if (8 === r.nodeType)
        if (r.data === o) d.push({ type: 2, index: c });
        else {
          let t = -1;
          for (; -1 !== (t = r.data.indexOf(h, t + 1)); )
            (d.push({ type: 7, index: c }), (t += h.length - 1));
        }
      c++;
    }
  }
  static createElement(t, i) {
    const s = r$1.createElement("template");
    return ((s.innerHTML = t), s);
  }
}
function S(t, i, s = t, e) {
  if (i === T) return i;
  let h = void 0 !== e ? s._$Co?.[e] : s._$Cl;
  const o = c(i) ? void 0 : i._$litDirective$;
  return (
    h?.constructor !== o &&
      (h?._$AO?.(false),
      void 0 === o ? (h = void 0) : ((h = new o(t)), h._$AT(t, s, e)),
      void 0 !== e ? ((s._$Co ??= [])[e] = h) : (s._$Cl = h)),
    void 0 !== h && (i = S(t, h._$AS(t, i.values), h, e)),
    i
  );
}
class M {
  constructor(t, i) {
    ((this._$AV = []), (this._$AN = void 0), (this._$AD = t), (this._$AM = i));
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const {
        el: { content: i },
        parts: s,
      } = this._$AD,
      e = (t?.creationScope ?? r$1).importNode(i, true);
    C.currentNode = e;
    let h = C.nextNode(),
      o = 0,
      n = 0,
      l = s[0];
    for (; void 0 !== l; ) {
      if (o === l.index) {
        let i;
        (2 === l.type
          ? (i = new R(h, h.nextSibling, this, t))
          : 1 === l.type
            ? (i = new l.ctor(h, l.name, l.strings, this, t))
            : 6 === l.type && (i = new z(h, this, t)),
          this._$AV.push(i),
          (l = s[++n]));
      }
      o !== l?.index && ((h = C.nextNode()), o++);
    }
    return ((C.currentNode = r$1), e);
  }
  p(t) {
    let i = 0;
    for (const s of this._$AV)
      (void 0 !== s &&
        (void 0 !== s.strings
          ? (s._$AI(t, s, i), (i += s.strings.length - 2))
          : s._$AI(t[i])),
        i++);
  }
}
class R {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, i, s, e) {
    ((this.type = 2),
      (this._$AH = E),
      (this._$AN = void 0),
      (this._$AA = t),
      (this._$AB = i),
      (this._$AM = s),
      (this.options = e),
      (this._$Cv = e?.isConnected ?? true));
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const i = this._$AM;
    return (void 0 !== i && 11 === t?.nodeType && (t = i.parentNode), t);
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, i = this) {
    ((t = S(this, t, i)),
      c(t)
        ? t === E || null == t || "" === t
          ? (this._$AH !== E && this._$AR(), (this._$AH = E))
          : t !== this._$AH && t !== T && this._(t)
        : void 0 !== t._$litType$
          ? this.$(t)
          : void 0 !== t.nodeType
            ? this.T(t)
            : u(t)
              ? this.k(t)
              : this._(t));
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), (this._$AH = this.O(t)));
  }
  _(t) {
    (this._$AH !== E && c(this._$AH)
      ? (this._$AA.nextSibling.data = t)
      : this.T(r$1.createTextNode(t)),
      (this._$AH = t));
  }
  $(t) {
    const { values: i, _$litType$: s } = t,
      e =
        "number" == typeof s
          ? this._$AC(t)
          : (void 0 === s.el &&
              (s.el = N.createElement(P(s.h, s.h[0]), this.options)),
            s);
    if (this._$AH?._$AD === e) this._$AH.p(i);
    else {
      const t = new M(e, this),
        s = t.u(this.options);
      (t.p(i), this.T(s), (this._$AH = t));
    }
  }
  _$AC(t) {
    let i = A.get(t.strings);
    return (void 0 === i && A.set(t.strings, (i = new N(t))), i);
  }
  k(t) {
    a(this._$AH) || ((this._$AH = []), this._$AR());
    const i = this._$AH;
    let s,
      e = 0;
    for (const h of t)
      (e === i.length
        ? i.push((s = new R(this.O(l()), this.O(l()), this, this.options)))
        : (s = i[e]),
        s._$AI(h),
        e++);
    e < i.length && (this._$AR(s && s._$AB.nextSibling, e), (i.length = e));
  }
  _$AR(t = this._$AA.nextSibling, i) {
    for (this._$AP?.(false, true, i); t && t !== this._$AB; ) {
      const i = t.nextSibling;
      (t.remove(), (t = i));
    }
  }
  setConnected(t) {
    void 0 === this._$AM && ((this._$Cv = t), this._$AP?.(t));
  }
}
class k {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, i, s, e, h) {
    ((this.type = 1),
      (this._$AH = E),
      (this._$AN = void 0),
      (this.element = t),
      (this.name = i),
      (this._$AM = e),
      (this.options = h),
      s.length > 2 || "" !== s[0] || "" !== s[1]
        ? ((this._$AH = Array(s.length - 1).fill(new String())),
          (this.strings = s))
        : (this._$AH = E));
  }
  _$AI(t, i = this, s, e) {
    const h = this.strings;
    let o = false;
    if (void 0 === h)
      ((t = S(this, t, i, 0)),
        (o = !c(t) || (t !== this._$AH && t !== T)),
        o && (this._$AH = t));
    else {
      const e = t;
      let n, r;
      for (t = h[0], n = 0; n < h.length - 1; n++)
        ((r = S(this, e[s + n], i, n)),
          r === T && (r = this._$AH[n]),
          (o ||= !c(r) || r !== this._$AH[n]),
          r === E ? (t = E) : t !== E && (t += (r ?? "") + h[n + 1]),
          (this._$AH[n] = r));
    }
    o && !e && this.j(t);
  }
  j(t) {
    t === E
      ? this.element.removeAttribute(this.name)
      : this.element.setAttribute(this.name, t ?? "");
  }
}
class H extends k {
  constructor() {
    (super(...arguments), (this.type = 3));
  }
  j(t) {
    this.element[this.name] = t === E ? void 0 : t;
  }
}
class I extends k {
  constructor() {
    (super(...arguments), (this.type = 4));
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== E);
  }
}
class L extends k {
  constructor(t, i, s, e, h) {
    (super(t, i, s, e, h), (this.type = 5));
  }
  _$AI(t, i = this) {
    if ((t = S(this, t, i, 0) ?? E) === T) return;
    const s = this._$AH,
      e =
        (t === E && s !== E) ||
        t.capture !== s.capture ||
        t.once !== s.once ||
        t.passive !== s.passive,
      h = t !== E && (s === E || e);
    (e && this.element.removeEventListener(this.name, this, s),
      h && this.element.addEventListener(this.name, this, t),
      (this._$AH = t));
  }
  handleEvent(t) {
    "function" == typeof this._$AH
      ? this._$AH.call(this.options?.host ?? this.element, t)
      : this._$AH.handleEvent(t);
  }
}
class z {
  constructor(t, i, s) {
    ((this.element = t),
      (this.type = 6),
      (this._$AN = void 0),
      (this._$AM = i),
      (this.options = s));
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    S(this, t);
  }
}
const j = t.litHtmlPolyfillSupport;
(j?.(N, R), (t.litHtmlVersions ??= []).push("3.2.1"));
const B = (t, i, s) => {
  const e = s?.renderBefore ?? i;
  let h = e._$litPart$;
  if (void 0 === h) {
    const t = s?.renderBefore ?? null;
    e._$litPart$ = h = new R(i.insertBefore(l(), t), t, void 0, s ?? {});
  }
  return (h._$AI(t), h);
};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */ class r extends b {
  constructor() {
    (super(...arguments),
      (this.renderOptions = { host: this }),
      (this._$Do = void 0));
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return ((this.renderOptions.renderBefore ??= t.firstChild), t);
  }
  update(t) {
    const s = this.render();
    (this.hasUpdated || (this.renderOptions.isConnected = this.isConnected),
      super.update(t),
      (this._$Do = B(s, this.renderRoot, this.renderOptions)));
  }
  connectedCallback() {
    (super.connectedCallback(), this._$Do?.setConnected(true));
  }
  disconnectedCallback() {
    (super.disconnectedCallback(), this._$Do?.setConnected(false));
  }
  render() {
    return T;
  }
}
((r._$litElement$ = true),
  (r["finalized"] = true),
  globalThis.litElementHydrateSupport?.({ LitElement: r }));
const i = globalThis.litElementPolyfillSupport;
i?.({ LitElement: r });
(globalThis.litElementVersions ??= []).push("4.1.1");

class IaiLitBase extends r {
  static styles = i$3`
        :root {
            --iai-colour-focus:  #ffdd04;
            --iai-colour-pink:  #C50878;
        }
    `;

  static properties = {
    encprops: { type: String },
  };

  constructor() {
    super();
    this.props = {};
  }

  createRenderRoot() {
    return this;
  }

  willUpdate() {
    if (this.encprops) {
      this.props = JSON.parse(atob(this.encprops)) || {};
    }
  }

  generateId(length = 16) {
    const startIndex = 2; //  skip the leading "0."
    return (
      "iai-" +
      Math.random()
        .toString(36)
        .substring(startIndex, startIndex + length)
    );
  }

  applyStaticStyles(componentTag, cssResult) {
    if (document.querySelector(`style[data-component="${componentTag}"]`)) {
      return;
    }

    const style = document.createElement("style");
    style.setAttribute("data-component", componentTag);

    // cssResult can be an array of cssResult objects, or a single cssResult object
    if (Array.isArray(cssResult)) {
      style.textContent = cssResult.map((result) => result.cssText).join("");
    } else {
      style.textContent = cssResult.cssText;
    }
    document.head.append(style);
  }
}

class IaiLitCsrExample extends IaiLitBase {
  static styles = [
    IaiLitBase.styles,
    i$3`
            span {
                color: salmon;
            }
        `,
  ];

  constructor() {
    super();
  }
  render() {
    return x`<p>Iai Lit <span>Csr</span> Component</p>`;
  }
}
customElements.define("iai-lit-csr-example", IaiLitCsrExample);

class IaiExpandingText extends IaiLitBase {
  static properties = {
    text: { type: String },
    lines: { type: Number },
    _expanded: { type: Boolean },
    _textOverflowing: { type: Boolean },
  };

  static styles = [
    IaiLitBase.styles,
    i$3`
            iai-expanding-text .iai-text-content {
                transition-property: color, padding-left;
                transition: 0.3s ease-in-out;
                padding-left: 0em;
                position: relative;
                width: 100%;
                line-height: 1.3em;
            }

            iai-expanding-text .iai-text-content.clickable {
                padding-left: 1em;
                cursor: pointer;
                transition-property: color;
                transition: 0.3s ease-in-out;
            }
            iai-expanding-text .iai-text-content.clickable:hover  {
                color: var(--iai-colour-pink);
            }
            iai-expanding-text .iai-text-content.clickable:focus-visible {
                outline: 3px solid var(--iai-colour-focus);
                border: 4px solid black;
            }
            iai-expanding-text .iai-text-content.clickable::before {
                content: "▸";
                position: absolute;
                left: 0;
                top: 0;
                transition: 0.3s ease-in-out;
                transition-property: transform;
            }

            iai-expanding-text .iai-text-content:not(.iai-text-truncated).clickable::before {
                transform: rotate(90deg);
            }
                
            iai-expanding-text .iai-text-content.iai-text-truncated {
                display: -webkit-box;
                display: box;

                -webkit-box-orient: vertical;
                box-orient: vertical;

                overflow: hidden;
                text-overflow: ellipsis;
            }
        `,
  ];

  constructor() {
    super();
    this.contentId = this.generateId();

    // Prop defaults
    this.text = "";
    this.lines = 1;
    this._expanded = false;
    this._textOverflowing = true;
  }

  handleClick() {
    if (!this._textOverflowing) {
      return;
    }
    this._expanded = !this._expanded;
  }

  isTextOverflowing = (element, lines) => {
    let computedLineHeight = parseInt(
      window.getComputedStyle(element).lineHeight,
    );
    const scrollHeight = this.querySelector(".iai-text-content").scrollHeight;
    return Math.round(scrollHeight / computedLineHeight) > lines;
  };

  updateTextOverflowing = () => {
    this._textOverflowing = this.isTextOverflowing(
      this.querySelector(".iai-text-content"),
      this.lines,
    );
  };

  firstUpdated() {
    this.applyStaticStyles("iai-expanding-text", IaiExpandingText.styles);

    this.updateTextOverflowing();

    window.addEventListener("resize", this.updateTextOverflowing);
  }

  updated(changedProps) {
    if (changedProps.has("lines") || changedProps.has("text")) {
      this.updateTextOverflowing();
    }
  }

  disconnectedCallback() {
    window.removeEventListener("resize", this.updateTextOverflowing);

    super.disconnectedCallback();
  }

  render() {
    return x`
            <style>
                .iai-text-content:has(#${this.contentId}).iai-text-truncated {
                    -webkit-line-clamp: ${this.lines};
                    line-clamp: ${this.lines};
                }
            </style>

            <div
                class=${
                  "iai-text-content" +
                  (this._textOverflowing ? " clickable" : "") +
                  (this._expanded ? "" : " iai-text-truncated")
                }
                role="button"
                aria-expanded=${this._expanded}
                aria-controls=${this.contentId}
                tabindex="0"
                @keydown=${(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    this.handleClick();
                  }
                }}
                @click=${this.handleClick}
            >
                <span id=${this.contentId}>
                    ${this.text}
                </span>
            </div>
        `;
  }
}
customElements.define("iai-expanding-text", IaiExpandingText);

class IaiTextWithFallback extends IaiLitBase {
  static properties = {
    ...IaiLitBase.properties,
    text: String,
    fallback: String,
    fallbackCondition: Function,
  };
  static styles = [
    IaiLitBase.styles,
    i$3`
            iai-text-with-fallback .fallback-active {
                font-style: italic;
            }
        `,
  ];

  constructor() {
    super();

    this.applyStaticStyles(
      "iai-text-with-fallback",
      IaiTextWithFallback.styles,
    );

    // By default, render fallback if text is falsy
    this.fallbackCondition = (text) => !text;
  }

  render() {
    return x`
            <p class=${this.fallbackCondition(this.text) ? "fallback-active" : ""}>
                ${this.fallbackCondition(this.text) ? this.fallback : this.text}
            </p>
        `;
  }
}
customElements.define("iai-text-with-fallback", IaiTextWithFallback);

class IaiDataTable extends IaiLitBase {
  static properties = {
    ...IaiLitBase.properties,
    data: { type: Array },
    _sortedData: { type: Array },
    _sorts: { type: Array },
  };

  static styles = [
    IaiLitBase.styles,
    i$3`
            iai-data-table .bottom-row td:first-child {
                font-weight: bold;
            }
            iai-data-table .header-button {
                position: relative;
                max-width: max-content;
                margin-right: 1em;
                transition: 0.3s ease-in-out;
                transition-property: color;
                cursor: pointer;
            }
            iai-data-table .header-button:hover {
                color: var(--iai-colour-pink);
            }
            iai-data-table .header-button:after {
                content: "▾";
                position: absolute;
                right: -1em;
                top: 0;
                opacity: 0;
                transition: 0.3s ease-in-out;
                transition-property: transform opacity;
            }
            iai-data-table .header-button.ascending:after {
                opacity: 1;
            }
            iai-data-table .header-button.descending:after {
                opacity: 1;
                transform: rotate(180deg);
            }
        `,
  ];

  constructor() {
    super();
    this.contentId = this.generateId();

    // These will not appear as column
    // as they merely act as flags for the row
    this._RESERVED_KEYS = ["_bottomRow"];

    // Prop defaults
    this.data = [];
    this._sorts = [];
    this._sortedData = [];
  }

  firstUpdated() {
    this.applyStaticStyles("iai-data-table", IaiDataTable.styles);

    this.updateSortedData();
  }

  updated(changedProps) {
    if (changedProps.has("_sorts") || changedProps.has("data")) {
      this.updateSortedData();
    }
  }

  getHeaders() {
    const keys = new Set();
    const data = this.props.data || this.data;

    data.forEach((row) => {
      Object.keys(row)
        .filter((key) => !this._RESERVED_KEYS.includes(key))
        .forEach((key) => keys.add(key));
    });
    return Array.from(keys);
  }

  updateSorts = (header) => {
    const updatedSorts = [...this._sorts];
    const sortIndex = updatedSorts.findIndex((sort) => sort.field === header);

    if (sortIndex === -1) {
      // If sort is not currently applied, apply sort in ascending order
      updatedSorts.unshift({ field: header, ascending: true });
    } else {
      // If sort is already applied
      const currentSort = updatedSorts[sortIndex];

      if (sortIndex === 0) {
        // If sort is the last to be applied, toggle direction
        currentSort.ascending = !currentSort.ascending;
      } else {
        // If sort is not last to be applied, update it's priority
        updatedSorts.splice(sortIndex, 1);
        updatedSorts.unshift({ field: header, ascending: true });
      }
    }

    this._sorts = updatedSorts;
  };

  sort(rows) {
    let result = [...rows];

    result.sort((rowA, rowB) => {
      for (const sort of this._sorts) {
        const direction = sort.ascending ? 1 : -1;

        const valA = rowA[sort.field];
        const valB = rowB[sort.field];

        if (typeof valA === "string") {
          // Sort strings alphabetically

          const compResult = valA.localeCompare(valB, undefined, {
            sensitivity: "base",
          });
          if (compResult !== 0) {
            return compResult * direction;
          }
        } else if (typeof valA === "number") {
          // Sort numbers numerically

          if (valA < valB) {
            return -1 * direction;
          }
          if (valA > valB) {
            return 1 * direction;
          }
        } else;
      }
      return 0;
    });

    return result;
  }

  updateSortedData() {
    // Rows that have a _bottomRow flag will appear at the bottom
    // and will be sorted as a separate group
    const data = this.props.data || this.data;

    const regularRows = data.filter((row) => !row._bottomRow);
    const bottomRows = data.filter((row) => row._bottomRow);

    this._sortedData = this.sort(regularRows).concat(this.sort(bottomRows));
  }

  getCurrentSortDirection = (header) => {
    const currentSortIndex = this._sorts.findIndex(
      (sort) => sort.field === header,
    );

    if (currentSortIndex === -1) {
      return "";
    }
    return this._sorts[currentSortIndex].ascending ? "ascending" : "descending";
  };

  render() {
    return x`
            <table class="govuk-table govuk-body" mentionstable="">
                <thead class="govuk-table__head">
                    <tr class="govuk-table__row">    
                        ${this.getHeaders().map(
                          (header) => x`
                            <th scope="col" class="govuk-table__header">
                                <div
                                    class=${"header-button " + this.getCurrentSortDirection(header)}
                                    role="button"
                                    aria-sort=${this.getCurrentSortDirection(header)}
                                    aria-label=${
                                      this.getCurrentSortDirection(header)
                                        ? `Sorted by "${header}" in ${this.getCurrentSortDirection(header)} order. Click to sort in reverse.`
                                        : `Click to sort by "${header}" in ascending order`
                                    }
                                    tabindex=0
                                    @click=${() => this.updateSorts(header)}
                                    @keydown=${(e) => {
                                      if (e.key === "Enter" || e.key === " ") {
                                        e.preventDefault();
                                        this.updateSorts(header);
                                      }
                                    }}
                                >
                                    ${header}
                                </div>
                            </th>
                        `,
                        )}
                    </tr>
                </thead>
          
                <tbody class="govuk-table__body">
                    ${this._sortedData.map(
                      (row) => x`
                        <tr class=${
                          "govuk-table__row" +
                          (row._bottomRow ? " bottom-row" : "")
                        }>
                            ${this.getHeaders().map(
                              (header) => x`
                                <td class="govuk-table__cell">
                                    ${row[header]}
                                </td>
                            `,
                            )}
                        </tr>
                    `,
                    )}
                </tbody>
            </table>
        `;
  }
}
customElements.define("iai-data-table", IaiDataTable);

class IaiCsvDownload extends IaiLitBase {
  static styles = [IaiLitBase.styles, i$3``];

  static properties = {
    ...IaiLitBase.properties,
    data: { type: Array },
    fileName: { type: String },
  };

  constructor() {
    super();

    this.data = [];
    this.fileName = "data.csv";
  }

  buildCsv(data) {
    if (!data) {
      return "";
    }

    const localData = Array.isArray(data) ? data : [data];

    const keys = Object.keys(data[0]);
    const rows = [
      keys.join(","),
      ...localData.map((row) =>
        keys.map((key) => JSON.stringify(row[key] ?? "")).join(","),
      ),
    ];
    return rows.join("\n");
  }

  getDownloadUrl = (csvContent) => {
    return "data:text/csv;base64," + btoa(csvContent);
  };

  render() {
    return x`
            <a
                class="govuk-button"
                aria-label="Download themes as CSV"
                title="Download themes as CSV"
                href=${this.getDownloadUrl(this.buildCsv(this.props.data || this.data))}
                download=${this.fileName}
            >
                Download CSV
            </a>
        `;
  }
}
customElements.define("iai-csv-download", IaiCsvDownload);
//# sourceMappingURL=bundle.js.map
