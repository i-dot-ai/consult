/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$2=globalThis,e$4=t$2.ShadowRoot&&(void 0===t$2.ShadyCSS||t$2.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$2=Symbol(),o$4=new WeakMap;let n$2 = class n{constructor(t,e,o){if(this._$cssResult$=true,o!==s$2)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$4&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=o$4.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&o$4.set(s,t));}return t}toString(){return this.cssText}};const r$2=t=>new n$2("string"==typeof t?t:t+"",void 0,s$2),i$4=(t,...e)=>{const o=1===t.length?t[0]:e.reduce(((e,s,o)=>e+(t=>{if(true===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[o+1]),t[0]);return new n$2(o,t,s$2)},S$1=(s,o)=>{if(e$4)s.adoptedStyleSheets=o.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet));else for(const e of o){const o=document.createElement("style"),n=t$2.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=e.cssText,s.appendChild(o);}},c$2=e$4?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$2(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:i$3,defineProperty:e$3,getOwnPropertyDescriptor:h$1,getOwnPropertyNames:r$1,getOwnPropertySymbols:o$3,getPrototypeOf:n$1}=Object,a$1=globalThis,c$1=a$1.trustedTypes,l$1=c$1?c$1.emptyScript:"",p$1=a$1.reactiveElementPolyfillSupport,d$1=(t,s)=>t,u$1={toAttribute(t,s){switch(s){case Boolean:t=t?l$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,s){let i=t;switch(s){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t);}catch(t){i=null;}}return i}},f$1=(t,s)=>!i$3(t,s),b={attribute:true,type:String,converter:u$1,reflect:false,useDefault:false,hasChanged:f$1};Symbol.metadata??=Symbol("metadata"),a$1.litPropertyMetadata??=new WeakMap;let y$1 = class y extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t);}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,s=b){if(s.state&&(s.attribute=false),this._$Ei(),this.prototype.hasOwnProperty(t)&&((s=Object.create(s)).wrapped=true),this.elementProperties.set(t,s),!s.noAccessor){const i=Symbol(),h=this.getPropertyDescriptor(t,i,s);void 0!==h&&e$3(this.prototype,t,h);}}static getPropertyDescriptor(t,s,i){const{get:e,set:r}=h$1(this.prototype,t)??{get(){return this[s]},set(t){this[s]=t;}};return {get:e,set(s){const h=e?.call(this);r?.call(this,s),this.requestUpdate(t,h,i);},configurable:true,enumerable:true}}static getPropertyOptions(t){return this.elementProperties.get(t)??b}static _$Ei(){if(this.hasOwnProperty(d$1("elementProperties")))return;const t=n$1(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties);}static finalize(){if(this.hasOwnProperty(d$1("finalized")))return;if(this.finalized=true,this._$Ei(),this.hasOwnProperty(d$1("properties"))){const t=this.properties,s=[...r$1(t),...o$3(t)];for(const i of s)this.createProperty(i,t[i]);}const t=this[Symbol.metadata];if(null!==t){const s=litPropertyMetadata.get(t);if(void 0!==s)for(const[t,i]of s)this.elementProperties.set(t,i);}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const i=this._$Eu(t,s);void 0!==i&&this._$Eh.set(i,t);}this.elementStyles=this.finalizeStyles(this.styles);}static finalizeStyles(s){const i=[];if(Array.isArray(s)){const e=new Set(s.flat(1/0).reverse());for(const s of e)i.unshift(c$2(s));}else void 0!==s&&i.push(c$2(s));return i}static _$Eu(t,s){const i=s.attribute;return  false===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=false,this.hasUpdated=false,this._$Em=null,this._$Ev();}_$Ev(){this._$ES=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach((t=>t(this)));}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.();}removeController(t){this._$EO?.delete(t);}_$E_(){const t=new Map,s=this.constructor.elementProperties;for(const i of s.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t);}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return S$1(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(true),this._$EO?.forEach((t=>t.hostConnected?.()));}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach((t=>t.hostDisconnected?.()));}attributeChangedCallback(t,s,i){this._$AK(t,i);}_$ET(t,s){const i=this.constructor.elementProperties.get(t),e=this.constructor._$Eu(t,i);if(void 0!==e&&true===i.reflect){const h=(void 0!==i.converter?.toAttribute?i.converter:u$1).toAttribute(s,i.type);this._$Em=t,null==h?this.removeAttribute(e):this.setAttribute(e,h),this._$Em=null;}}_$AK(t,s){const i=this.constructor,e=i._$Eh.get(t);if(void 0!==e&&this._$Em!==e){const t=i.getPropertyOptions(e),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:u$1;this._$Em=e;const r=h.fromAttribute(s,t.type);this[e]=r??this._$Ej?.get(e)??r,this._$Em=null;}}requestUpdate(t,s,i){if(void 0!==t){const e=this.constructor,h=this[t];if(i??=e.getPropertyOptions(t),!((i.hasChanged??f$1)(h,s)||i.useDefault&&i.reflect&&h===this._$Ej?.get(t)&&!this.hasAttribute(e._$Eu(t,i))))return;this.C(t,s,i);} false===this.isUpdatePending&&(this._$ES=this._$EP());}C(t,s,{useDefault:i,reflect:e,wrapped:h},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??s??this[t]),true!==h||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(s=void 0),this._$AL.set(t,s)),true===e&&this._$Em!==t&&(this._$Eq??=new Set).add(t));}async _$EP(){this.isUpdatePending=true;try{await this._$ES;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,s]of this._$Ep)this[t]=s;this._$Ep=void 0;}const t=this.constructor.elementProperties;if(t.size>0)for(const[s,i]of t){const{wrapped:t}=i,e=this[s];true!==t||this._$AL.has(s)||void 0===e||this.C(s,void 0,i,e);}}let t=false;const s=this._$AL;try{t=this.shouldUpdate(s),t?(this.willUpdate(s),this._$EO?.forEach((t=>t.hostUpdate?.())),this.update(s)):this._$EM();}catch(s){throw t=false,this._$EM(),s}t&&this._$AE(s);}willUpdate(t){}_$AE(t){this._$EO?.forEach((t=>t.hostUpdated?.())),this.hasUpdated||(this.hasUpdated=true,this.firstUpdated(t)),this.updated(t);}_$EM(){this._$AL=new Map,this.isUpdatePending=false;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return  true}update(t){this._$Eq&&=this._$Eq.forEach((t=>this._$ET(t,this[t]))),this._$EM();}updated(t){}firstUpdated(t){}};y$1.elementStyles=[],y$1.shadowRootOptions={mode:"open"},y$1[d$1("elementProperties")]=new Map,y$1[d$1("finalized")]=new Map,p$1?.({ReactiveElement:y$1}),(a$1.reactiveElementVersions??=[]).push("2.1.1");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1=globalThis,i$2=t$1.trustedTypes,s$1=i$2?i$2.createPolicy("lit-html",{createHTML:t=>t}):void 0,e$2="$lit$",h=`lit$${Math.random().toFixed(9).slice(2)}$`,o$2="?"+h,n=`<${o$2}>`,r=document,l=()=>r.createComment(""),c=t=>null===t||"object"!=typeof t&&"function"!=typeof t,a=Array.isArray,u=t=>a(t)||"function"==typeof t?.[Symbol.iterator],d="[ \t\n\f\r]",f=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,v=/-->/g,_=/>/g,m=RegExp(`>|${d}(?:([^\\s"'>=/]+)(${d}*=${d}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),p=/'/g,g=/"/g,$=/^(?:script|style|textarea|title)$/i,y=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),x=y(1),T=Symbol.for("lit-noChange"),E=Symbol.for("lit-nothing"),A=new WeakMap,C=r.createTreeWalker(r,129);function P(t,i){if(!a(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==s$1?s$1.createHTML(i):i}const V=(t,i)=>{const s=t.length-1,o=[];let r,l=2===i?"<svg>":3===i?"<math>":"",c=f;for(let i=0;i<s;i++){const s=t[i];let a,u,d=-1,y=0;for(;y<s.length&&(c.lastIndex=y,u=c.exec(s),null!==u);)y=c.lastIndex,c===f?"!--"===u[1]?c=v:void 0!==u[1]?c=_:void 0!==u[2]?($.test(u[2])&&(r=RegExp("</"+u[2],"g")),c=m):void 0!==u[3]&&(c=m):c===m?">"===u[0]?(c=r??f,d=-1):void 0===u[1]?d=-2:(d=c.lastIndex-u[2].length,a=u[1],c=void 0===u[3]?m:'"'===u[3]?g:p):c===g||c===p?c=m:c===v||c===_?c=f:(c=m,r=void 0);const x=c===m&&t[i+1].startsWith("/>")?" ":"";l+=c===f?s+n:d>=0?(o.push(a),s.slice(0,d)+e$2+s.slice(d)+h+x):s+h+(-2===d?i:x);}return [P(t,l+(t[s]||"<?>")+(2===i?"</svg>":3===i?"</math>":"")),o]};class N{constructor({strings:t,_$litType$:s},n){let r;this.parts=[];let c=0,a=0;const u=t.length-1,d=this.parts,[f,v]=V(t,s);if(this.el=N.createElement(f,n),C.currentNode=this.el.content,2===s||3===s){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes);}for(;null!==(r=C.nextNode())&&d.length<u;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(e$2)){const i=v[a++],s=r.getAttribute(t).split(h),e=/([.?@])?(.*)/.exec(i);d.push({type:1,index:c,name:e[2],strings:s,ctor:"."===e[1]?H:"?"===e[1]?I:"@"===e[1]?L:k}),r.removeAttribute(t);}else t.startsWith(h)&&(d.push({type:6,index:c}),r.removeAttribute(t));if($.test(r.tagName)){const t=r.textContent.split(h),s=t.length-1;if(s>0){r.textContent=i$2?i$2.emptyScript:"";for(let i=0;i<s;i++)r.append(t[i],l()),C.nextNode(),d.push({type:2,index:++c});r.append(t[s],l());}}}else if(8===r.nodeType)if(r.data===o$2)d.push({type:2,index:c});else {let t=-1;for(;-1!==(t=r.data.indexOf(h,t+1));)d.push({type:7,index:c}),t+=h.length-1;}c++;}}static createElement(t,i){const s=r.createElement("template");return s.innerHTML=t,s}}function S(t,i,s=t,e){if(i===T)return i;let h=void 0!==e?s._$Co?.[e]:s._$Cl;const o=c(i)?void 0:i._$litDirective$;return h?.constructor!==o&&(h?._$AO?.(false),void 0===o?h=void 0:(h=new o(t),h._$AT(t,s,e)),void 0!==e?(s._$Co??=[])[e]=h:s._$Cl=h),void 0!==h&&(i=S(t,h._$AS(t,i.values),h,e)),i}class M{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:i},parts:s}=this._$AD,e=(t?.creationScope??r).importNode(i,true);C.currentNode=e;let h=C.nextNode(),o=0,n=0,l=s[0];for(;void 0!==l;){if(o===l.index){let i;2===l.type?i=new R(h,h.nextSibling,this,t):1===l.type?i=new l.ctor(h,l.name,l.strings,this,t):6===l.type&&(i=new z(h,this,t)),this._$AV.push(i),l=s[++n];}o!==l?.index&&(h=C.nextNode(),o++);}return C.currentNode=r,e}p(t){let i=0;for(const s of this._$AV) void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}}class R{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,i,s,e){this.type=2,this._$AH=E,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cv=e?.isConnected??true;}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t?.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=S(this,t,i),c(t)?t===E||null==t||""===t?(this._$AH!==E&&this._$AR(),this._$AH=E):t!==this._$AH&&t!==T&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):u(t)?this.k(t):this._(t);}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}_(t){this._$AH!==E&&c(this._$AH)?this._$AA.nextSibling.data=t:this.T(r.createTextNode(t)),this._$AH=t;}$(t){const{values:i,_$litType$:s}=t,e="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=N.createElement(P(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===e)this._$AH.p(i);else {const t=new M(e,this),s=t.u(this.options);t.p(i),this.T(s),this._$AH=t;}}_$AC(t){let i=A.get(t.strings);return void 0===i&&A.set(t.strings,i=new N(t)),i}k(t){a(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const h of t)e===i.length?i.push(s=new R(this.O(l()),this.O(l()),this,this.options)):s=i[e],s._$AI(h),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){for(this._$AP?.(false,true,i);t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){ void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t));}}class k{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,i,s,e,h){this.type=1,this._$AH=E,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=h,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=E;}_$AI(t,i=this,s,e){const h=this.strings;let o=false;if(void 0===h)t=S(this,t,i,0),o=!c(t)||t!==this._$AH&&t!==T,o&&(this._$AH=t);else {const e=t;let n,r;for(t=h[0],n=0;n<h.length-1;n++)r=S(this,e[s+n],i,n),r===T&&(r=this._$AH[n]),o||=!c(r)||r!==this._$AH[n],r===E?t=E:t!==E&&(t+=(r??"")+h[n+1]),this._$AH[n]=r;}o&&!e&&this.j(t);}j(t){t===E?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"");}}class H extends k{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===E?void 0:t;}}class I extends k{constructor(){super(...arguments),this.type=4;}j(t){this.element.toggleAttribute(this.name,!!t&&t!==E);}}class L extends k{constructor(t,i,s,e,h){super(t,i,s,e,h),this.type=5;}_$AI(t,i=this){if((t=S(this,t,i,0)??E)===T)return;const s=this._$AH,e=t===E&&s!==E||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,h=t!==E&&(s===E||e);e&&this.element.removeEventListener(this.name,this,s),h&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t);}}class z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t);}}const j=t$1.litHtmlPolyfillSupport;j?.(N,R),(t$1.litHtmlVersions??=[]).push("3.3.1");const B=(t,i,s)=>{const e=s?.renderBefore??i;let h=e._$litPart$;if(void 0===h){const t=s?.renderBefore??null;e._$litPart$=h=new R(i.insertBefore(l(),t),t,void 0,s??{});}return h._$AI(t),h};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const s=globalThis;let i$1 = class i extends y$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const r=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=B(r,this.renderRoot,this.renderOptions);}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(true);}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(false);}render(){return T}};i$1._$litElement$=true,i$1["finalized"]=true,s.litElementHydrateSupport?.({LitElement:i$1});const o$1=s.litElementPolyfillSupport;o$1?.({LitElement:i$1});(s.litElementVersions??=[]).push("4.2.1");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t={CHILD:2},e$1=t=>(...e)=>({_$litDirective$:t,values:e});class i{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i;}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class e extends i{constructor(i){if(super(i),this.it=E,i.type!==t.CHILD)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(r){if(r===E||null==r)return this._t=void 0,this.it=r;if(r===T)return r;if("string"!=typeof r)throw Error(this.constructor.directiveName+"() called with a non-string value");if(r===this.it)return this._t;this.it=r;const s=[r];return s.raw=s,this._t={_$litType$:this.constructor.resultType,strings:s,values:[]}}}e.directiveName="unsafeHTML",e.resultType=1;const o=e$1(e);

class IaiLitBase extends i$1 {
    static styles = i$4`
        :root {
            --iai-colour-focus:  #ffdd04;
            --iai-colour-pink:  #C50878;
            --iai-colour-secondary: #0B8478;
            --iai-colour-secondary-transparent: #0b84781a;
            --iai-colour-pink-transparent: #c5087812;
            --iai-colour-pink-transparent-mid: #F0B5D8;

            --iai-silver-color-light: #f8f9fa;
            --iai-silver-color-light-darker: #f3f3f5;
            --iai-silver-color-mid-light: #e5e5e5;
            --iai-silver-color-mid: rgba(0, 0, 0, 0.3);
            --iai-silver-color-dark: #030213;
            --iai-silver-color-text: rgb(95, 99, 104);
            --iai-silver-color-teal: #00786f;
            --iai-silver-color-teal-mid: #85d07e;
            --iai-silver-color-teal-light: #f1fdfa;
            --iai-silver-color-accent: #c50978;
            --iai-silver-color-accent-light: #fcf1f6;
            --iai-silver-color-amber: #ba4d00;
            --iai-silver-color-amber-mid: #ffe020;
            --iai-silver-color-amber-light: #fffbea;
            --iai-silver-color-pink: rgb(131, 24, 67);
            --iai-silver-color-pink-mid: rgb(197, 8, 120);
            --iai-silver-color-pink-light: rgb(253, 242, 248);
        }

        .visually-hidden {
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 0;
            overflow: hidden;
        }

        .matched-text {
            background: yellow;
        }
    `

    static properties = {
        encprops: {type: String},
    }

    constructor() {
        super();
        this.props = {};

        this.CONSULTATION_STATUSES = {
            open: "Open",
            analysing: "Analysing",
            completed: "Completed",
            closed: "Closed",
        };
        this._STORAGE_KEYS = {
            FAVOURITE_QUESTIONS: "favouriteQuestions",
        };
    }
    
    createRenderRoot() {
        return this;
    }

    willUpdate() {
        if (this.encprops) {
            this.props = JSON.parse(atob(this.encprops)) || {};
        }
    }

    generateId(length=16) {
        const startIndex = 2; //  skip the leading "0."
        return "iai-" + Math.random().toString(36).substring(startIndex, startIndex+length);
    }

    applyStaticStyles(componentTag, cssResult) {
        if (document.querySelector(`style[data-component="${componentTag}"]`)) {
            return;
        }

        const style = document.createElement("style");
        style.setAttribute("data-component", componentTag);

        // cssResult can be an array of cssResult objects, or a single cssResult object
        if (Array.isArray(cssResult)) {
            style.textContent = cssResult.map(result => result.cssText).join("");
        } else {
            style.textContent = cssResult.cssText;
        }
        document.head.append(style);
    }

    applySlots = (slotName) => {
        Promise.resolve().then(() => {
            const slottedChildren = this.querySelectorAll(`:scope > [slot='${slotName}']`);
            const slot = this.querySelector(`slot[name='${slotName}']`);
            slottedChildren.forEach(child => slot.appendChild(child));
        });
    }

    accessibleKeyPressed = (key) => {
        return key === "Enter" || key === " ";
    }

    getPercentage = (partialValue, totalValue) => {
        if (totalValue === 0) {
            return 0;
        }
        const percentage = (partialValue / totalValue) * 100;

        // Round to 1 decimal point
        return Math.round(percentage * 10) / 10;
    }

    toTitleCase = (text) => {
        return text
            .replace("-", " ")
            .replace(
                /\w\S*/g,
                text => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
            );
    }

    getHighlightedText = (fullText, matchedText) => {
        if (!matchedText) {
            return fullText;
        }
        const regex = new RegExp(matchedText, "gi");
        return fullText.replace(regex, match => `<span class="matched-text">${match}</span>`);
    }

    limitChars = (text, maxChars) => {
        return text.length > maxChars
            ? text.substring(0, maxChars) + "..."
            : text
    }

    toggleStorage = (newValue, storageKey) => {
        let existingValues = this.getStoredValues(storageKey);

        if (existingValues.includes(newValue)) {
            existingValues = existingValues.filter(value => value !== newValue);
        } else {
            existingValues.push(newValue);
        }
        localStorage.setItem(storageKey, JSON.stringify(existingValues));
    }

    getStoredValues = (storageKey) => {
        const storedValue = localStorage.getItem(storageKey);
        return storedValue ? JSON.parse(storedValue) : [];
    }
}

class IaiExpandingText extends IaiLitBase {
    static properties = {
        text: { type: String },
        lines: { type: Number },
        _expanded: { type: Boolean },
        _textOverflowing: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
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
        `
    ]

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
        let computedLineHeight = parseInt(window.getComputedStyle(element).lineHeight);
        const scrollHeight = this.querySelector(".iai-text-content").scrollHeight;
        return Math.round(scrollHeight / computedLineHeight) > lines;
    }

    updateTextOverflowing = () => {
        this._textOverflowing = this.isTextOverflowing(
            this.querySelector(".iai-text-content"),
            this.lines
        );
    } 

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
                class=${"iai-text-content"
                    + (this._textOverflowing ? " clickable" : "")
                    + (this._expanded ? "" : " iai-text-truncated")
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
                    ${o(this.text)}
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
    }
    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-text-with-fallback .fallback-active {
                font-style: italic;
            }
        `
    ]

    constructor() {
        super();

        this.applyStaticStyles("iai-text-with-fallback", IaiTextWithFallback.styles);
        
        // By default, render fallback if text is falsy
        this.fallbackCondition = (text) => !text;
    }

    render() {
        return x`
            <p class=${this.fallbackCondition(this.text) ? "fallback-active" : ""}>
                ${this.fallbackCondition(this.text) ? this.fallback : this.text}
            </p>
        `
    }
}
customElements.define("iai-text-with-fallback", IaiTextWithFallback);

class IaiIcon extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        name: { type: String },
        color: { type: String },
        fill: {type: Number }, //  0 | 1
        opsz: { type: Number },
        wght: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-icon {
                display: flex;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Google expect icon names to be alphabetically sorted
        this._ALL_ICON_NAMES = ["visibility", "close", "star", "search", "thumb_up", "thumb_down", "thumbs_up_down", "arrow_drop_down_circle", "download", "diamond", "progress_activity", "sort", "schedule", "calendar_month", "group", "description", "monitoring", "settings", "help", "chat_bubble", "wand_stars", "lan", "finance", "filter_alt", "network_intelligence", "arrow_downward", "arrow_upward", "report", "chevron_left", "keyboard_arrow_down"];
        this._URL = "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=" + [...this._ALL_ICON_NAMES].sort().join(",");

        // Prop defaults
        this.name = "";
        this.color = "";
        this.fill = 0;
        this.opsz = 48;
        this.wght = 300;
        
        this.applyStaticStyles("iai-icon", IaiIcon.styles);
    }

    firstUpdated() {
        this.addIconImport();
    }

    addIconImport() {
        // Do not add if already added
        if (document.querySelector(`link[href="${this._URL}"]`)) {
            return;
        }

        const linkElement = document.createElement("link");
        linkElement.rel = "stylesheet";
        linkElement.href = this._URL;
        document.head.append(linkElement);
    }

    render() {
        return x`
            <style>
                #${this.contentId}.material-symbols-outlined {
                    font-variation-settings:
                        'FILL' ${this.fill},
                        'opsz' ${this.opsz},
                        'wght' ${this.wght};
                    color: ${this.color};
                }
            </style>
            <span id=${this.contentId} class="material-symbols-outlined">
                ${this.name}
            </span>
        `;
    }
}
customElements.define("iai-icon", IaiIcon);

class Button extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: { type: String },
        handleClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-button button {
                background: white;
                outline: none;
                border: 1px solid var(--iai-silver-color-mid-light);
                padding: 0.5em 1em;
                border-radius: 0.5em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-silver-button button:hover {
                background: var(--iai-silver-color-light);
            }
            iai-silver-button button:focus-visible {
                outline: 3px solid #fd0;
                outline-offset: 0;
                box-shadow: inset 0 0 0 2px;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "white";
        this.handleClick = () => {};

        this.applyStaticStyles("iai-silver-button", Button.styles);
    }

    render() {
        return x`
            <button @click=${this.handleClick}>
                ${this.text}
            </button>
        `
    }
}
customElements.define("iai-silver-button", Button);

class IaiCsvDownload extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-csv-download a {
                text-decoration: none;
            }
            iai-csv-download a.govuk-button {
                min-height: auto;
                min-width: 13em;
                justify-content: center;
            }
            iai-csv-download iai-silver-button button {
                padding-block: 0.25em;
            }
        `
    ]

    static properties = {
        ...IaiLitBase.properties,
        data: {type: Array},
        fileName: { type: String },
        variant: { type: String }, // "" | "silver"
    }

    constructor() {
        super();

        this.data = [];
        this.fileName = "data.csv";
        this.variant = "";

        this.applyStaticStyles("iai-csv-download", IaiCsvDownload.styles);
    }

    buildCsv(data) {
        if (!data || !Object.keys(data).length > 0) {
            return "";
        }

        const localData = Array.isArray(data) ? data : [data];
        
        const keys = Object.keys(data[0]);
        const rows = [
            keys.join(","),
            ...localData.map(row => keys.map(key => JSON.stringify(row[key] ?? "")).join(","))
        ];
        return rows.join("\n");
    }

    getDownloadUrl = (csvContent) => {
        return "data:text/csv;base64," + btoa(csvContent);
    }

    render() {
        return x`
            <a
                class=${!this.variant ? "govuk-button" : ""}
                aria-label="Download themes as CSV"
                title="Download themes as CSV"
                href=${this.getDownloadUrl(this.buildCsv(this.props.data || this.data))}
                download=${this.fileName}
            >
                ${this.variant === "silver"
                    ? x`
                        <iai-silver-button
                            .icon=${"download"}
                            .text=${x`
                                <iai-icon
                                    name="download"
                                ></iai-icon>
                                <span>
                                    Export
                                </span>
                            `}
                        ></iai-silver-button>
                    `
                    : x`
                        Download CSV
                        <iai-icon
                            name="download"
                        ></iai-icon>
                    `}
            </a>
        `
    }
}
customElements.define("iai-csv-download", IaiCsvDownload);

class IaiIconButton extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        handleClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-icon-button button {
                background: none;
                border: none;
                cursor: pointer;
                border-radius: 0.5em;
                padding: 0.3em 0.5em;
                transition: 0.3s ease-in-out;
                transition-property: background-color, color;
            }
            iai-icon-button button:hover {
                color: black;
                background: #cbfbf1;
            }
            iai-icon-button iai-icon {
                font-size: 1.2em;
            }
            iai-icon-button iai-icon iai-icon {
                position: absolute;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._SLOT_NAMES = ["icon"];

        // Prop defaults
        this.title = "";
        this.handleClick = () => {};
        
        this.applyStaticStyles("iai-icon-button", IaiIconButton.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return x`
            <button
                type="button"
                title=${this.title}
                @click=${this.handleClick}
            >
                <slot name="icon"></slot>
            </button>
        `;
    }
}
customElements.define("iai-icon-button", IaiIconButton);

class IaiPageTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        subtitle: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.subtitle = "";
        
        this.applyStaticStyles("iai-page-title", IaiPageTitle.styles);
    }

    render() {
        return x`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <h2 class="govuk-heading-s">${this.subtitle}</h2>
                    <h1 class="govuk-heading-l">${this.title}</h1>
                </div>
            </div>
        `;
    }
}
customElements.define("iai-page-title", IaiPageTitle);

class IaiProgressBar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        value: { type: Number },
        label: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-progress-bar .container {
                border: 1px dotted;
            }
            iai-progress-bar .container .bar {
                display: flex;
                justify-content: end;
                align-items: center;
                position: relative;
                height: 2em;
                color: white;
                transition: width 1s ease-in-out;
                background: var(--iai-colour-pink);
            }
            iai-progress-bar .container .label {
                display: block;    
                position: absolute;
                right: 0.5em;
                text-align: right;
                color: white;
                font-weight: bold;
            }
            iai-progress-bar .container.low-value .label {
                left: calc(100% + 0.5em);
                color: var(--iai-colour-pink);
                font-size: 1.2em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.value = 0;
        this.label = "";
        
        this.applyStaticStyles("iai-progress-bar", IaiProgressBar.styles);
    }

    getWidth() {
        if (this.value > 100) {
            return 100;
        }
        if (this.value < 0) {
            return 0;
        }
        return this.value;
    }

    render() {
        return x`
            <div class=${"container" + (this.value < 30 ? " low-value" : "")}>
                <div class=${"bar" + (this.value >= 100 ? " full" : "")} style=${`width: ${this.getWidth()}%;`}>
                    ${this.label
                        ? x`
                            <span class="label">
                                ${this.label}
                            </span>
                        `
                        : ""
                    }
                </div>
            </div>
        `;
    }
}
customElements.define("iai-progress-bar", IaiProgressBar);

class ProgressBar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        value: { type: Number },
        variant: { type: String }, //  "primary" | "secondary"
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-progress-bar {
                flex-grow: 1;
            }
            iai-silver-progress-bar iai-progress-bar .container {
                border-radius: 0.5em;
                background: var(--iai-silver-color-mid);
                border: none;
                opacity: 0.7;
            }
            iai-silver-progress-bar .bar {
                height: 0.5em;
                border-top-left-radius: 0.5em;
                border-bottom-left-radius: 0.5em;
                background: var(--iai-silver-color-dark);
            }
            iai-silver-progress-bar iai-progress-bar.primary .bar {
                background: var(--iai-silver-color-accent);
            }
            iai-silver-progress-bar iai-progress-bar.primary .container {
                background: var(--iai-silver-color-mid-light);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this.value = 0;
        this.variant = "primary";
        
        this.applyStaticStyles("iai-silver-progress-bar", ProgressBar.styles);
    }

    render() {
        return x`
            <iai-progress-bar
                class=${this.variant === "primary" ? "primary" : "secondary"}
                .value=${this.value}
                .label=${""}
            ></iai-progress-bar>
        `;
    }
}
customElements.define("iai-silver-progress-bar", ProgressBar);

class IconTile extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        color: { type: String },
        backgroundColor: { type: String },
        name: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-icon-tile {
                display: block;    
                width: max-content;
            }
            iai-silver-icon-tile .icon-tile-container {
                display: flex;    
                justify-content: center;
                align-items: center;
                background: salmon;
                padding: 0.4em;
                border-radius: 0.5em;
            }
            iai-silver-icon-tile .material-symbols-outlined {
                font-size: 2em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.color = "white";
        this.backgroundColor = "black";
        this.name = "";

        this.applyStaticStyles("iai-silver-icon-tile", IconTile.styles);
    }

    render() {
        return x`
            <style>
                #${this.contentId} {
                    color: ${this.color};
                    background: ${this.backgroundColor};
                }
            </style>
            <div id=${this.contentId} class="icon-tile-container">
                <iai-icon
                    .name=${this.name}
                ></iai-icon>
            </div>
        `
    }
}
customElements.define("iai-silver-icon-tile", IconTile);

class Title extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        level: { type: Number },
        text: { type: String },
        subtext: { type: String },
        icon: { type: String },
        aside: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-title h1,
            iai-silver-title h2,
            iai-silver-title h3,
            iai-silver-title h4 {
                margin: 0;
            }
            iai-silver-title h1 {
                font-size: 1.3em;
            }
            iai-silver-title h2 {
                font-size: 1em;
            }
            iai-silver-title h3,
            iai-silver-title h4 {
                font-size: 0.9em;
            }
            iai-silver-title .container {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }
            iai-silver-title .icon-container {
                display: flex;
                align-items: center;
                gap: 0.5em;
                margin-bottom: 1.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.level = 2;
        this.text = "";
        this.subtext = "";
        this.icon = "";
        this.aside = "";

        this.applyStaticStyles("iai-silver-title", Title.styles);
    }

    renderTitleTag = () => {
        switch (this.level) {
            case 1:
                return x`<h1>${this.text}</h1>`;
            case 2:
                return x`<h2>${this.text}</h2>`;
            case 3:
                return x`<h3>${this.text}</h3>`;
            case 4:
                return x`<h4>${this.text}</h4>`;
        }
    }

    render() {
        return x`
        <div class="container">
            <div class="icon-container">
                ${this.icon
                    ? x`
                        <iai-silver-icon-tile
                            .backgroundColor=${"var(--iai-silver-color-accent-light)"}
                            .color=${"var(--iai-silver-color-accent)"}
                            .name=${this.icon}
                        ></iai-silver-icon-tile>
                    `
                    : ""
                }

                <div>
                    ${this.renderTitleTag()}

                    ${this.subtext
                        ? x`
                            <small>
                                ${this.subtext}
                            </small>
                        `
                        : ""
                    }
                </div>
            </div>

            <aside>
                ${this.aside}
            </aside>
        </div>
        `
    }
}
customElements.define("iai-silver-title", Title);

class ProgressCard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        data: { type: Object }, //  key/value pairs
        _totalCount: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-progress-card article {
                height: 100%;
                max-height: 40em;
                overflow: auto;
                padding: 1em;
                font-size: 1em;
                color: var(--iai-silver-color-text);
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
            }
            iai-progress-card ul {
                display: flex;
                flex-direction: column;
                gap: 1.5em;
                margin: 0;
                padding-left: 0;
                font-weight: bold;
                font-size: 0.9em;
            }
            iai-progress-card li {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-direction: column;
                list-style: none;
                line-height: 1.5em;
                gap: 0.5em;
            }
            iai-progress-card li>* {
                width: 100%;
                word-wrap: break-word;
            }
            iai-progress-card li .percentage {
                font-size: 0.8em;
                color: rgba(0, 0, 0, 0.5);
            }
            iai-progress-card li .count {
                font-size: 1.2em;
            }
            iai-progress-card li {
                font-size: 0.9em;
                color: rgba(0, 0, 0, 0.6);
            }
            iai-progress-card .info {
                display: flex;
                gap: 0.5em;
            }
            iai-progress-card .label {
                font-size: 0.9em;
            }
            iai-progress-card .counts {
                display: flex;
                align-items: center;
                gap: 1em;
                font-weight: normal;
                font-size: 0.8em;
            }
            
            iai-progress-card iai-silver-progress-bar .container,
            iai-progress-card iai-silver-progress-bar .container .bar {
                height: 0.6em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.data = {};
        this._totalCount = 0;
        
        this.applyStaticStyles("iai-progress-card", ProgressCard.styles);
    }

    updated(changedProps) {
        if (changedProps.has("data")) {
            this._totalCount = Object.values(this.data).reduce( (a, b) => a + b, 0 );
        }
    }

    render() {
        return x`
            <article>
                ${this.title ? x`
                    <iai-silver-title
                        .text=${this.title}
                        .level=${3}
                    ></iai-silver-title>
                ` : ""}

                <ul>
                    ${Object.keys(this.data).map(key => {
                        const label = key;
                        const count = this.data[key];
                        const percentage = this.getPercentage(count, this._totalCount);

                        return x`
                            <li>
                                <div class="info">
                                    <span class="label">
                                        ${label}
                                    </span>
                                    <span class="count">
                                        ${count.toLocaleString()}
                                    </span>
                                    <span class="percentage">
                                        ${percentage}%
                                    </span>
                                </div>

                                <div>
                                    <iai-silver-progress-bar
                                        .value=${percentage}
                                    ></iai-silver-progress-bar>
                                </div>
                            </li>
                        `
                    })}
                </ul>
            </article>
        `
    }
}
customElements.define("iai-progress-card", ProgressCard);

class Panel extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        borderColor: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-panel .panel {
                padding: 1em;
                border: 1px solid;
                border-radius: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        // Prop defaults
        this.borderColor = "";

        this.applyStaticStyles("iai-silver-panel", Panel.styles);
    }

    updated() {
        this.applySlots("content");
    }

    render() {
        return x`
            <style>
                #${this.contentId} {
                    border-color: ${this.borderColor || "var(--iai-silver-color-mid-light)"};
                }
            </style>
            <div id=${this.contentId} class="panel">
                <slot name="content"></slot>
            </div>
        `
    }
}
customElements.define("iai-silver-panel", Panel);

class ProgressCards extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
        title: { type: String },
        subtitle: { type: String },
        themeFilters: { type: Array },
        demoFilters: { type: Object},
        total: { type: Number },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4` 
            iai-progress-cards .cards {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                max-width: 100%;
                overflow: auto;
            }    
            iai-progress-cards iai-progress-card {
                flex-grow: 1;
                max-width: 100%;
            }
            .themes-warning .tag {
                width: 100%;
                margin-bottom: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._MAX_DEMO_ANSWERS = 10;

        // Prop defaults
        this.title = "";
        this.subtitle = "";
        this.data = [];
        this.themeFilters = [];
        this.demoFilters = {};
        this.total = 0;

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};
        
        this.applyStaticStyles("iai-progress-cards", ProgressCards.styles);
    }

    getFilterWarningText() {
        const demoFiltersText = Object
            .values(this.demoFilters)
            .flat(1)
            .filter(Boolean)
            .join(", ");

        const themeFiltersText = this.themeFilters.length
            ? `${this.themeFilters.length} themes`
            : "";

        return [demoFiltersText, themeFiltersText].filter(Boolean).join(", ");
    }

    render() {
        return x`
            <iai-silver-panel>
                <div slot="content">
                    <div class="top-panel">
                        <iai-silver-title
                            .text=${this.title}
                            .subtext=${this.subtitle}
                            .icon=${"group"}
                            .level=${2}
                        ></iai-silver-title>

                        ${this.themeFiltersApplied() || this.demoFiltersApplied()
                            ? x`
                                <iai-silver-tag
                                    class="themes-warning"
                                    .text=${"Active theme analysis filters"}
                                    .subtext=${`Showing data for ${this.total.toLocaleString()} responses (filtered by: ${this.getFilterWarningText()})`}
                                    .icon=${"report"}
                                    .status=${"Analysing"}
                                ></iai-silver-tag>
                            `
                            : ""
                        }

                        <div class="cards">
                            ${Object.keys(this.data).map(category => {
                                return Object.values(this.data[category]).length <= this._MAX_DEMO_ANSWERS
                                    ? x`
                                        <iai-progress-card
                                            .title=${this.toTitleCase(category)}
                                            .data=${this.data[category]}
                                        ></iai-progress-card>
                                    ` : ""})}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-progress-cards", ProgressCards);

class IaiAnimatedNumber extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        number: { type: Number },
        duration: { type: Number }, // miliseconds
        _displayNumber: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.number = 0;
        this.duration = 1000;
        this._displayNumber = 0;
        
        this.applyStaticStyles("iai-animated-number", IaiAnimatedNumber.styles);
    }

    setDisplayNumber = (newDisplayNumber) => {
        this._displayNumber = newDisplayNumber;
    }

    animate = (start, end, duration) => {
        const setDisplayNumber = (newDisplayNumber) => {
            this._displayNumber = newDisplayNumber;
        };
        const startTime = performance.now();

        function update_number(currTime) {
            const elapsedTime = currTime - startTime;
            const time = Math.min(elapsedTime / duration, 1);
            const currValue = start * (1 - time) + end * time;

            // round to 1 decimal point
            setDisplayNumber(Math.round(currValue * 10) / 10);

            if (time < 1) {
                requestAnimationFrame(update_number);
            }
        }

        requestAnimationFrame(update_number);
    }

    updated(changedProps) {
        if (changedProps.has("number")) {
            this.animate(this._displayNumber, this.number, this.duration);
        }
    }

    render() {
        return x`
            <span>${this._displayNumber}</span>
        `;
    }
}
customElements.define("iai-animated-number", IaiAnimatedNumber);

class IaiLoadingIndicator extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-loading-indicator .spinner {
                display: flex;
                justify-content: center;
                animation-name: spin;
                animation-duration: 1s;
                animation-iteration-count: infinite;
                animation-timing-function: ease-in-out;
            }
            iai-loading-indicator .spinner iai-icon .material-symbols-outlined {
                font-size: 3em;
            }

            @keyframes spin {
                from {
                    transform:rotate(0deg);
                }
                to {
                    transform:rotate(360deg);
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this.applyStaticStyles("iai-loading-indicator", IaiLoadingIndicator.styles);
    }

    render() {
        return x`
            <div class="spinner">
                <iai-icon
                    name="progress_activity"
                    .opsz=${48}
                    .color=${"var(--iai-colour-pink)"}
                ></iai-icon>
            </div>
        `;
    }
}
customElements.define("iai-loading-indicator", IaiLoadingIndicator);
//# sourceMappingURL=index.js.map
