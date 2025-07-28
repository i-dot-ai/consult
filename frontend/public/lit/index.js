/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$3=globalThis,e$4=t$3.ShadowRoot&&(void 0===t$3.ShadyCSS||t$3.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$4=Symbol(),o$6=new WeakMap;let n$4 = class n{constructor(t,e,o){if(this._$cssResult$=true,o!==s$4)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$4&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=o$6.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&o$6.set(s,t));}return t}toString(){return this.cssText}};const r$5=t=>new n$4("string"==typeof t?t:t+"",void 0,s$4),i$4=(t,...e)=>{const o=1===t.length?t[0]:e.reduce(((e,s,o)=>e+(t=>{if(true===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[o+1]),t[0]);return new n$4(o,t,s$4)},S$1=(s,o)=>{if(e$4)s.adoptedStyleSheets=o.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet));else for(const e of o){const o=document.createElement("style"),n=t$3.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=e.cssText,s.appendChild(o);}},c$4=e$4?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$5(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:i$3,defineProperty:e$3,getOwnPropertyDescriptor:h$2,getOwnPropertyNames:r$4,getOwnPropertySymbols:o$5,getPrototypeOf:n$3}=Object,a$1=globalThis,c$3=a$1.trustedTypes,l$1=c$3?c$3.emptyScript:"",p$2=a$1.reactiveElementPolyfillSupport,d$1=(t,s)=>t,u$3={toAttribute(t,s){switch(s){case Boolean:t=t?l$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,s){let i=t;switch(s){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t);}catch(t){i=null;}}return i}},f$3=(t,s)=>!i$3(t,s),b={attribute:true,type:String,converter:u$3,reflect:false,useDefault:false,hasChanged:f$3};Symbol.metadata??=Symbol("metadata"),a$1.litPropertyMetadata??=new WeakMap;let y$1 = class y extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t);}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,s=b){if(s.state&&(s.attribute=false),this._$Ei(),this.prototype.hasOwnProperty(t)&&((s=Object.create(s)).wrapped=true),this.elementProperties.set(t,s),!s.noAccessor){const i=Symbol(),h=this.getPropertyDescriptor(t,i,s);void 0!==h&&e$3(this.prototype,t,h);}}static getPropertyDescriptor(t,s,i){const{get:e,set:r}=h$2(this.prototype,t)??{get(){return this[s]},set(t){this[s]=t;}};return {get:e,set(s){const h=e?.call(this);r?.call(this,s),this.requestUpdate(t,h,i);},configurable:true,enumerable:true}}static getPropertyOptions(t){return this.elementProperties.get(t)??b}static _$Ei(){if(this.hasOwnProperty(d$1("elementProperties")))return;const t=n$3(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties);}static finalize(){if(this.hasOwnProperty(d$1("finalized")))return;if(this.finalized=true,this._$Ei(),this.hasOwnProperty(d$1("properties"))){const t=this.properties,s=[...r$4(t),...o$5(t)];for(const i of s)this.createProperty(i,t[i]);}const t=this[Symbol.metadata];if(null!==t){const s=litPropertyMetadata.get(t);if(void 0!==s)for(const[t,i]of s)this.elementProperties.set(t,i);}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const i=this._$Eu(t,s);void 0!==i&&this._$Eh.set(i,t);}this.elementStyles=this.finalizeStyles(this.styles);}static finalizeStyles(s){const i=[];if(Array.isArray(s)){const e=new Set(s.flat(1/0).reverse());for(const s of e)i.unshift(c$4(s));}else void 0!==s&&i.push(c$4(s));return i}static _$Eu(t,s){const i=s.attribute;return  false===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=false,this.hasUpdated=false,this._$Em=null,this._$Ev();}_$Ev(){this._$ES=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach((t=>t(this)));}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.();}removeController(t){this._$EO?.delete(t);}_$E_(){const t=new Map,s=this.constructor.elementProperties;for(const i of s.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t);}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return S$1(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(true),this._$EO?.forEach((t=>t.hostConnected?.()));}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach((t=>t.hostDisconnected?.()));}attributeChangedCallback(t,s,i){this._$AK(t,i);}_$ET(t,s){const i=this.constructor.elementProperties.get(t),e=this.constructor._$Eu(t,i);if(void 0!==e&&true===i.reflect){const h=(void 0!==i.converter?.toAttribute?i.converter:u$3).toAttribute(s,i.type);this._$Em=t,null==h?this.removeAttribute(e):this.setAttribute(e,h),this._$Em=null;}}_$AK(t,s){const i=this.constructor,e=i._$Eh.get(t);if(void 0!==e&&this._$Em!==e){const t=i.getPropertyOptions(e),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:u$3;this._$Em=e,this[e]=h.fromAttribute(s,t.type)??this._$Ej?.get(e)??null,this._$Em=null;}}requestUpdate(t,s,i){if(void 0!==t){const e=this.constructor,h=this[t];if(i??=e.getPropertyOptions(t),!((i.hasChanged??f$3)(h,s)||i.useDefault&&i.reflect&&h===this._$Ej?.get(t)&&!this.hasAttribute(e._$Eu(t,i))))return;this.C(t,s,i);} false===this.isUpdatePending&&(this._$ES=this._$EP());}C(t,s,{useDefault:i,reflect:e,wrapped:h},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??s??this[t]),true!==h||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(s=void 0),this._$AL.set(t,s)),true===e&&this._$Em!==t&&(this._$Eq??=new Set).add(t));}async _$EP(){this.isUpdatePending=true;try{await this._$ES;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,s]of this._$Ep)this[t]=s;this._$Ep=void 0;}const t=this.constructor.elementProperties;if(t.size>0)for(const[s,i]of t){const{wrapped:t}=i,e=this[s];true!==t||this._$AL.has(s)||void 0===e||this.C(s,void 0,i,e);}}let t=false;const s=this._$AL;try{t=this.shouldUpdate(s),t?(this.willUpdate(s),this._$EO?.forEach((t=>t.hostUpdate?.())),this.update(s)):this._$EM();}catch(s){throw t=false,this._$EM(),s}t&&this._$AE(s);}willUpdate(t){}_$AE(t){this._$EO?.forEach((t=>t.hostUpdated?.())),this.hasUpdated||(this.hasUpdated=true,this.firstUpdated(t)),this.updated(t);}_$EM(){this._$AL=new Map,this.isUpdatePending=false;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return  true}update(t){this._$Eq&&=this._$Eq.forEach((t=>this._$ET(t,this[t]))),this._$EM();}updated(t){}firstUpdated(t){}};y$1.elementStyles=[],y$1.shadowRootOptions={mode:"open"},y$1[d$1("elementProperties")]=new Map,y$1[d$1("finalized")]=new Map,p$2?.({ReactiveElement:y$1}),(a$1.reactiveElementVersions??=[]).push("2.1.0");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$2=globalThis,i$2=t$2.trustedTypes,s$3=i$2?i$2.createPolicy("lit-html",{createHTML:t=>t}):void 0,e$2="$lit$",h$1=`lit$${Math.random().toFixed(9).slice(2)}$`,o$4="?"+h$1,n$2=`<${o$4}>`,r$3=document,l=()=>r$3.createComment(""),c$2=t=>null===t||"object"!=typeof t&&"function"!=typeof t,a=Array.isArray,u$2=t=>a(t)||"function"==typeof t?.[Symbol.iterator],d="[ \t\n\f\r]",f$2=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,v$1=/-->/g,_=/>/g,m$1=RegExp(`>|${d}(?:([^\\s"'>=/]+)(${d}*=${d}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),p$1=/'/g,g=/"/g,$=/^(?:script|style|textarea|title)$/i,y=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),x=y(1),T=Symbol.for("lit-noChange"),E=Symbol.for("lit-nothing"),A=new WeakMap,C=r$3.createTreeWalker(r$3,129);function P(t,i){if(!a(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==s$3?s$3.createHTML(i):i}const V=(t,i)=>{const s=t.length-1,o=[];let r,l=2===i?"<svg>":3===i?"<math>":"",c=f$2;for(let i=0;i<s;i++){const s=t[i];let a,u,d=-1,y=0;for(;y<s.length&&(c.lastIndex=y,u=c.exec(s),null!==u);)y=c.lastIndex,c===f$2?"!--"===u[1]?c=v$1:void 0!==u[1]?c=_:void 0!==u[2]?($.test(u[2])&&(r=RegExp("</"+u[2],"g")),c=m$1):void 0!==u[3]&&(c=m$1):c===m$1?">"===u[0]?(c=r??f$2,d=-1):void 0===u[1]?d=-2:(d=c.lastIndex-u[2].length,a=u[1],c=void 0===u[3]?m$1:'"'===u[3]?g:p$1):c===g||c===p$1?c=m$1:c===v$1||c===_?c=f$2:(c=m$1,r=void 0);const x=c===m$1&&t[i+1].startsWith("/>")?" ":"";l+=c===f$2?s+n$2:d>=0?(o.push(a),s.slice(0,d)+e$2+s.slice(d)+h$1+x):s+h$1+(-2===d?i:x);}return [P(t,l+(t[s]||"<?>")+(2===i?"</svg>":3===i?"</math>":"")),o]};class N{constructor({strings:t,_$litType$:s},n){let r;this.parts=[];let c=0,a=0;const u=t.length-1,d=this.parts,[f,v]=V(t,s);if(this.el=N.createElement(f,n),C.currentNode=this.el.content,2===s||3===s){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes);}for(;null!==(r=C.nextNode())&&d.length<u;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(e$2)){const i=v[a++],s=r.getAttribute(t).split(h$1),e=/([.?@])?(.*)/.exec(i);d.push({type:1,index:c,name:e[2],strings:s,ctor:"."===e[1]?H:"?"===e[1]?I:"@"===e[1]?L:k}),r.removeAttribute(t);}else t.startsWith(h$1)&&(d.push({type:6,index:c}),r.removeAttribute(t));if($.test(r.tagName)){const t=r.textContent.split(h$1),s=t.length-1;if(s>0){r.textContent=i$2?i$2.emptyScript:"";for(let i=0;i<s;i++)r.append(t[i],l()),C.nextNode(),d.push({type:2,index:++c});r.append(t[s],l());}}}else if(8===r.nodeType)if(r.data===o$4)d.push({type:2,index:c});else {let t=-1;for(;-1!==(t=r.data.indexOf(h$1,t+1));)d.push({type:7,index:c}),t+=h$1.length-1;}c++;}}static createElement(t,i){const s=r$3.createElement("template");return s.innerHTML=t,s}}function S(t,i,s=t,e){if(i===T)return i;let h=void 0!==e?s._$Co?.[e]:s._$Cl;const o=c$2(i)?void 0:i._$litDirective$;return h?.constructor!==o&&(h?._$AO?.(false),void 0===o?h=void 0:(h=new o(t),h._$AT(t,s,e)),void 0!==e?(s._$Co??=[])[e]=h:s._$Cl=h),void 0!==h&&(i=S(t,h._$AS(t,i.values),h,e)),i}let M$1 = class M{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:i},parts:s}=this._$AD,e=(t?.creationScope??r$3).importNode(i,true);C.currentNode=e;let h=C.nextNode(),o=0,n=0,l=s[0];for(;void 0!==l;){if(o===l.index){let i;2===l.type?i=new R(h,h.nextSibling,this,t):1===l.type?i=new l.ctor(h,l.name,l.strings,this,t):6===l.type&&(i=new z(h,this,t)),this._$AV.push(i),l=s[++n];}o!==l?.index&&(h=C.nextNode(),o++);}return C.currentNode=r$3,e}p(t){let i=0;for(const s of this._$AV) void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}};class R{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,i,s,e){this.type=2,this._$AH=E,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cv=e?.isConnected??true;}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t?.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=S(this,t,i),c$2(t)?t===E||null==t||""===t?(this._$AH!==E&&this._$AR(),this._$AH=E):t!==this._$AH&&t!==T&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):u$2(t)?this.k(t):this._(t);}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}_(t){this._$AH!==E&&c$2(this._$AH)?this._$AA.nextSibling.data=t:this.T(r$3.createTextNode(t)),this._$AH=t;}$(t){const{values:i,_$litType$:s}=t,e="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=N.createElement(P(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===e)this._$AH.p(i);else {const t=new M$1(e,this),s=t.u(this.options);t.p(i),this.T(s),this._$AH=t;}}_$AC(t){let i=A.get(t.strings);return void 0===i&&A.set(t.strings,i=new N(t)),i}k(t){a(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const h of t)e===i.length?i.push(s=new R(this.O(l()),this.O(l()),this,this.options)):s=i[e],s._$AI(h),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){for(this._$AP?.(false,true,i);t&&t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){ void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t));}}class k{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,i,s,e,h){this.type=1,this._$AH=E,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=h,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=E;}_$AI(t,i=this,s,e){const h=this.strings;let o=false;if(void 0===h)t=S(this,t,i,0),o=!c$2(t)||t!==this._$AH&&t!==T,o&&(this._$AH=t);else {const e=t;let n,r;for(t=h[0],n=0;n<h.length-1;n++)r=S(this,e[s+n],i,n),r===T&&(r=this._$AH[n]),o||=!c$2(r)||r!==this._$AH[n],r===E?t=E:t!==E&&(t+=(r??"")+h[n+1]),this._$AH[n]=r;}o&&!e&&this.j(t);}j(t){t===E?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"");}}class H extends k{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===E?void 0:t;}}class I extends k{constructor(){super(...arguments),this.type=4;}j(t){this.element.toggleAttribute(this.name,!!t&&t!==E);}}class L extends k{constructor(t,i,s,e,h){super(t,i,s,e,h),this.type=5;}_$AI(t,i=this){if((t=S(this,t,i,0)??E)===T)return;const s=this._$AH,e=t===E&&s!==E||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,h=t!==E&&(s===E||e);e&&this.element.removeEventListener(this.name,this,s),h&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t);}}class z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t);}}const Z={I:R},j=t$2.litHtmlPolyfillSupport;j?.(N,R),(t$2.litHtmlVersions??=[]).push("3.3.0");const B=(t,i,s)=>{const e=s?.renderBefore??i;let h=e._$litPart$;if(void 0===h){const t=s?.renderBefore??null;e._$litPart$=h=new R(i.insertBefore(l(),t),t,void 0,s??{});}return h._$AI(t),h};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const s$2=globalThis;let i$1 = class i extends y$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const r=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=B(r,this.renderRoot,this.renderOptions);}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(true);}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(false);}render(){return T}};i$1._$litElement$=true,i$1["finalized"]=true,s$2.litElementHydrateSupport?.({LitElement:i$1});const o$3=s$2.litElementPolyfillSupport;o$3?.({LitElement:i$1});(s$2.litElementVersions??=[]).push("4.2.0");

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

class IaiLitCsrExample extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        i$4`
            span {
                color: salmon;
            }
        `
    ]

    constructor() {
        super();
    }
    render() {
        return x`<p>Iai Lit <span>Csr</span> Component</p>`
    }
}
customElements.define("iai-lit-csr-example", IaiLitCsrExample);

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1={CHILD:2},e$1=t=>(...e)=>({_$litDirective$:t,values:e});class i{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i;}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class e extends i{constructor(i){if(super(i),this.it=E,i.type!==t$1.CHILD)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(r){if(r===E||null==r)return this._t=void 0,this.it=r;if(r===T)return r;if("string"!=typeof r)throw Error(this.constructor.directiveName+"() called with a non-string value");if(r===this.it)return this._t;this.it=r;const s=[r];return s.raw=s,this._t={_$litType$:this.constructor.resultType,strings:s,values:[]}}}e.directiveName="unsafeHTML",e.resultType=1;const o$2=e$1(e);

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
                    ${o$2(this.text)}
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

class IaiDataTable extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
        initialSorts: { type: Array },
        sortable: { type: Boolean },
        _sortedData: { type: Array },
        _sorts: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-data-table h3 {
                margin: 0;
                font-size: 1em;
            }
            iai-data-table tbody.govuk-table__body td {
                vertical-align: middle;
            }
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
            iai-data-table thead {
                text-align: start;
            }
            iai-data-table thead th {
                text-align: left;
                margin-right: 1em;
                padding-right: 2em;
                position: relative;
            }
            iai-data-table .header-button iai-icon {
                position: absolute;
                top: 0;
                right: 0.5em;
                opacity: 0;
                transition: 0.3s ease-in-out;
                transition-property: transform, opacity;
            }
            iai-data-table thead .header-button:hover iai-icon {
                opacity: 0.5;
            }
            iai-data-table thead .header-button.ascending iai-icon,
            iai-data-table thead .header-button.descending iai-icon {
                opacity: 1;
            }
            iai-data-table thead .header-button.ascending iai-icon {
                transform: rotateX(180deg);
            }
            iai-data-table tr.clickable-row {
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-data-table tr.clickable-row:hover {
                background: rgba(0, 0, 0, 0.05);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // These will not appear as column
        // as they merely act as flags for the row
        this._RESERVED_KEYS = ["_bottomRow", "_sortValues", "_handleClick"];

        // Prop defaults
        this.data = [];
        this.sortable = true;
        this._sorts = [];
        this._sortedData = [];
    }

    firstUpdated() {
        this.applyStaticStyles("iai-data-table", IaiDataTable.styles);

        if (this.initialSorts) {
            this._sorts = this.initialSorts;
        }

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

        data.forEach(row => {
            Object.keys(row)
            .filter(key => !this._RESERVED_KEYS.includes(key))
            .forEach(key => keys.add(key));
        });
        return Array.from(keys);
    }

    updateSorts = (header) => {
        const updatedSorts = [...this._sorts];
        const sortIndex = updatedSorts.findIndex(sort => sort.field === header);

        if (sortIndex === -1) {
            // If sort is not currently applied, apply sort in ascending order
            updatedSorts.unshift({ "field": header, "ascending": true });

        } else {
            // If sort is already applied
            const currentSort = updatedSorts[sortIndex];

            if (sortIndex === 0) {
                // If sort is the last to be applied
                if (currentSort.ascending) {
                    // if ascending make it descending
                    currentSort.ascending = false;
                } else {
                    // if descending order, unapply it
                    updatedSorts.splice(sortIndex, 1);
                }

            } else {
                // If sort is not last to be applied, update it's priority
                updatedSorts.splice(sortIndex, 1);
                updatedSorts.unshift({ "field": header, "ascending": true });
            }
        }

        this._sorts = updatedSorts;
    }

    sort(rows) {
        let result = [...rows];

        result.sort((rowA, rowB) => {
            for (const sort of this._sorts) {
                const direction = sort.ascending ? 1 : -1;

                // If _sortValues specified, use that for sorting instead
                const valA = (rowA._sortValues && rowA._sortValues[sort.field]) || rowA[sort.field];
                const valB = (rowB._sortValues && rowB._sortValues[sort.field]) || rowB[sort.field];

                if (typeof valA === "string") {
                    // Sort strings alphabetically

                    const compResult = valA.localeCompare(valB, undefined, {sensitivity: "base"});
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
                } else ;
            }
            return 0;
        });
        
        return result;
    }

    updateSortedData() {
        // Rows that have a _bottomRow flag will appear at the bottom
        // and will be sorted as a separate group
        const data = this.props.data || this.data;

        const regularRows = data.filter(row => !row._bottomRow);
        const bottomRows = data.filter(row => row._bottomRow);

        this._sortedData = this.sort(regularRows).concat(this.sort(bottomRows));
    }

    getCurrentSortDirection = (header) => {
        const currentSortIndex = this._sorts.findIndex(sort => sort.field === header);

        if (currentSortIndex === -1) {
            return "";
        }
        return this._sorts[currentSortIndex].ascending ? "ascending" : "descending";
    }

    renderHeader = (header) => {
        if (!this.sortable) {
            return x`
                <th
                    scope="col"
                    class="govuk-table__header"
                >
                    <h3>${header}</h3>
                </th>
            `
        }
        return x`
            <th
                style="" scope="col" class="govuk-table__header"
                class=${"header-button " + this.getCurrentSortDirection(header)}
                role="button"
                aria-sort=${this.getCurrentSortDirection(header)}
                aria-label=${this.getCurrentSortDirection(header)
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
                <h3>${header}</h3>
                <iai-icon
                    name="sort"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>
            </th>
        `
    }

    render() {
        const data = this.sortable ? this._sortedData : this.data;

        return x`
            <table class="govuk-table govuk-body" mentionstable="">
                <thead class="govuk-table__head">
                    <tr class="govuk-table__row">    
                        ${this.getHeaders().map(header => this.renderHeader(header))}
                    </tr>
                </thead>
          
                <tbody class="govuk-table__body">
                    ${data.map(row => x`
                        <tr
                            class=${"govuk-table__row"
                                + (row._bottomRow ? " bottom-row" : "")
                                + (row._handleClick ? " clickable-row" : "")
                            }
                            @click=${row._handleClick || undefined}
                        >
                            ${this.getHeaders().map(header => x`
                                <td class="govuk-table__cell">
                                    ${row[header]}
                                </td>
                            `)}
                        </tr>
                    `)}
                </tbody>
            </table>
        `;
    }
}
customElements.define("iai-data-table", IaiDataTable);

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

class IaiRadioInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        label: { type: String },
        checked: {type: Boolean },
        value: { type: String },
        handleChange: { type: Function },
        name: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-radio-input .govuk-radios__item:last-child,
            iai-radio-input .govuk-radios__item:last-of-type {
                margin-bottom: 10px;
            }
            iai-radio-input .govuk-radios__label, .govuk-radios__hint {
                padding-bottom: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.label = "";
        this.checked = false;
        this.value = "";
        this.handleChange = () => {};
        this.name = "";

        this.applyStaticStyles("iai-radio-input", IaiRadioInput.styles);
    }

    render() {
        return x`
            <div class="govuk-radios__item">
                <input
                    type="radio"
                    class="govuk-radios__input"
                    id=${this.inputId}
                    name=${this.name}
                    ?checked=${this.checked}
                    value=${this.value}
                    @change=${this.handleChange}
                />

                <label
                    class="govuk-label govuk-radios__label"
                    for=${this.inputId}
                >
                    ${this.label}
                </label>
            </div>
        `
    }
}
customElements.define("iai-radio-input", IaiRadioInput);

class IaiResponseFilters extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._SLOT_NAMES = ["filters"];

        this.applyStaticStyles("iai-response-filters", IaiResponseFilters.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return x`
            <div class="iai-filter">
                <div class="iai-filter__header">
                    <div class="iai-filter__header-title">
                        <h2 class="govuk-heading-m">
                            Filter
                        </h2>
                    </div>
                </div>

                <slot name="filters"></slot>
            </div>
        `;
    }
}
customElements.define("iai-response-filters", IaiResponseFilters);

class IaiNumberInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
        placeholder: { type: String },
        value: { type: String },
        handleInput: { type: Function },
        horizontal: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-number-input .horizontal {
                display: flex;
                align-items: center;
                gap: 0.5em;
            }
            iai-number-input .horizontal label {
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.placeholder = "";
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-number-input", IaiNumberInput.styles);
    }

    render() {
        return x`
            <div class=${this.horizontal ? "horizontal" : ""}>
                <label class="govuk-label govuk-label--m" for=${this.inputId}>
                    ${this.label}
                </label>
                <input
                    type="number"
                    class="govuk-input"
                    id=${this.inputId}
                    name=${this.name}
                    placeholder=${this.placeholder}
                    value=${this.value}
                    @input=${this.handleInput}
                />
            </div>
        `
    }
}
customElements.define("iai-number-input", IaiNumberInput);

class IaiCheckboxInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        label: { type: String },
        hideLabel: { type: Boolean },
        checked: {type: Boolean },
        value: { type: String },
        handleChange: { type: Function },
        name: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-checkbox-input .govuk-radios__item:last-child,
            iai-checkbox-input .govuk-radios__item:last-of-type {
                margin-bottom: 10px;
            }
            iai-checkbox-input .govuk-radios__label, .govuk-radios__hint {
                padding-bottom: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.hideLabel = false;
        this.label = "";
        this.checked = false;
        this.value = "";
        this.handleChange = () => {};
        this.name = "";

        this.applyStaticStyles("iai-checkbox-input", IaiCheckboxInput.styles);
    }

    updated(changedProps) {
        if (changedProps.has("checked")) {
            this.querySelector("input").checked = this.checked;
        }
    }

    render() {
        return x`
            <div class="govuk-checkboxes__item">
                <input
                    type="checkbox"
                    class="govuk-checkboxes__input"
                    id=${this.inputId}
                    name=${this.name}
                    value=${this.value}
                    @change=${this.handleChange}
                >
                <label
                    class="govuk-label govuk-checkboxes__label"
                    for=${this.inputId}
                >
                    ${this.hideLabel ? "" : this.label}
                </label>
            </div>
        `
    }
}
customElements.define("iai-checkbox-input", IaiCheckboxInput);

class IaiResponsesTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        total: {type: Number},
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.total = 0;
        
        this.applyStaticStyles("iai-responses-title", IaiResponsesTitle.styles);
    }

    render() {
        return x`
            <div class="govuk-grid-row">
                <div class="govuk-grid-column-full">
                    <span class="govuk-caption-m">
                        ${this.total} responses
                    </span>
                    <h2 class="govuk-heading-m">
                        Individual responses
                    </h2>
                </div>
            </div>
        `;
    }
}
customElements.define("iai-responses-title", IaiResponsesTitle);

class IaiExpandingPill extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        label: {type: String},
        body: {type: String},
        initialExpanded: {type: Boolean},
        _expanded: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-expanding-pill {
                font-size: 0.9em;
            }
            
            iai-expanding-pill button {
                display: flex;
                justify-content: space-between;
                align-items: center;
                text-align: start;
                padding: 0.3em 0.8em;
                gap: 1em;
                font-size: 1em;
                background: #c50878;
                color: white;
                border: none;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
            }
            iai-expanding-pill button.expanded iai-icon {
                transition: transform 0.3s ease-in-out;
                transform: rotate(180deg);
            }
            iai-expanding-pill .body {
                font-size: 1.1em;
                line-height: 1.8em;
                padding: 0 0.5em;
                margin-bottom: 0.5em;
                max-height: 0;
                overflow: hidden;
                transition: 0.6s ease;
                transition-property: max-height, padding;
            }
            iai-expanding-pill .body.expanded {
                padding-block: 0.5em;
                max-height: 10em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.label = "";
        this.body = "";
        this.initialExpanded = false;
        this._expanded = false;

        this.applyStaticStyles("iai-expanding-pill", IaiExpandingPill.styles);
    }

    firstUpdated() {
        this._expanded = this.initialExpanded;
    }

    render() {
        return x`    
            <button
                class=${this._expanded ? "expanded" : ""}
                @click=${_ => this._expanded = !this._expanded}
            >
                ${this.label}
                <iai-icon
                    .name=${"arrow_drop_down_circle"}
                    .opsz=${12}
                ></iai-icon>
            </button>
            <div class=${"body" + (this._expanded ? " expanded" : "")}>
                ${this.body}
            </div>
        `;
    }
}
customElements.define("iai-expanding-pill", IaiExpandingPill);

class IaiResponse extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        identifier: {type: String},
        free_text_answer_text: {type: String},
        themes: {type: Array}, // theme.stance, theme.name, theme.description
        sentiment_position: {type: String},
        demographic_data: {type: String}, // ?
        has_multiple_choice_question_part: {type: Boolean},
        multiple_choice_answer: {type: Array},
        searchValue: {type: String},
        evidenceRich: {type: Boolean},
        skeleton: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-response {
                width: 100%;
            }

            iai-response .matched-text {
                background-color: yellow;
            }

            iai-response .sentiment-position {
                display: flex;
                align-items: center;
                gap: 0.6%;
            }

            iai-response .sentiment-position img {
                width: 24px;
                height: 24px;
            }

            iai-response .answer,
            iai-response .answer {
                line-height: 2em;
            }

            iai-response .themes tool-tip,
            iai-response .themes tool-tip .iai-tooltip__button img {
                width: 14px;
            }
            iai-response .themes tool-tip .iai-tooltip__button {
                gap: 0.5em;
            }
            iai-response iai-expanding-text .iai-text-content {
                transition: none;
            }
            iai-response .response {
                border: 2px solid var(--iai-colour-border-grey);
            }
            iai-response .themes {
                margin-bottom: 1em;
            }
            iai-response .space-between {
                display: flex;
                justify-content: space-between;
                width: 100%;
            }
            iai-response iai-icon .material-symbols-outlined {
                font-size: 2em;
            }
            iai-response .demographic-data ul {
                display: flex;
                flex-direction: column;
            }
            iai-response .skeleton {
                background: black;
                color: transparent;
                animation: fadeInOut 1s ease-in-out infinite alternate;
                user-select: none;
                pointer-events: none;
            }
            @keyframes fadeInOut {
                from {
                    opacity: 0.1;
                }
                to {
                    opacity: 0.2;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.identifier = "";
        this.free_text_answer_text = "";
        this.themes = [];
        this.sentiment_position = "";
        this.demographic_data = undefined;
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_answer = [];
        this.searchValue = "";
        this.evidenceRich = false;
        this.skeleton = false;

        this.applyStaticStyles("iai-response", IaiResponse.styles);
    }

    renderSentimentIcon = () => {
        const url = "https://consult.ai.cabinetoffice.gov.uk/static/icons/";

        if (this.sentiment_position == "AGREEMENT") {
            return x`<img src="${url + "thumbs-up.svg"}" alt="icon" />`;
        }
        if (this.sentiment_position == "DISAGREEMENT") {
            return x`<img src="${url + "thumbs-down.svg"}" alt="icon" />`;
        }
        return x`<img src="${url + "thumbs-up-down.svg"}" alt="icon" />`;
    }

    getFormattedSentiment = () => {
        if (this.sentiment_position == "AGREEMENT") {
            return x`<strong>Agree</strong> with the question`;
        } else if (this.sentiment_position == "DISAGREEMENT") {
            return x`<strong>Disagree</strong> with the question`;
        } else if (this.sentiment_position == "UNCLEAR") {
            return x`<strong>Unclear</strong> about the question`;
        }    }

    getHighlightedText = (fullText, matchedText) => {
        if (!matchedText) {
            return fullText;
        }
        const regex = new RegExp(matchedText, "gi");
        return fullText.replace(regex, match => `<span class="matched-text">${match}</span>`);
    }

    render() {
        return x`
            <div class="iai-panel response govuk-!-margin-bottom-4">
                <div class="govuk-grid-row">
                    <div class="govuk-grid-column-two-thirds space-between">
                        <h2 class=${"govuk-heading-m" + (this.skeleton ? " skeleton" : "")}>
                            Respondent ${this.identifier}
                        </h2>

                        ${this.evidenceRich
                            ? x`
                                <iai-icon
                                    title="Evidence-rich response"
                                    name="diamond"
                                    .opsz=${48}
                                ></iai-icon>
                            `
                            : ""
                        }
                    </div>
                </div>

                ${this.free_text_answer_text
                    ? x`
                        <p
                            class=${"govuk-body answer" + (this.skeleton ? " skeleton" : "")}
                            data-testid="free-text-answer"
                        >
                            <iai-expanding-text
                                .text=${this.getHighlightedText(this.free_text_answer_text, this.searchValue)}
                                .lines=${2}
                            ></iai-expanding-text>
                        </p>

                        ${this.sentiment_position
                            ? x`
                                <p class="govuk-body sentiment-position">
                                    ${this.renderSentimentIcon()}
                                    <span>
                                        ${this.getFormattedSentiment()}
                                    </span>
                                </p>
                            `
                            : ""
                        }

                        <div class="themes">
                            ${Array.isArray(this.themes)
                                ? this.themes.map(theme => x`
                                    <iai-expanding-pill
                                        .label=${theme.name}
                                        .body=${theme.description}
                                        .initialExpanded=${false}
                                    ></iai-expanding-pill>
                                `)
                                : ""}
                        </div>
                    `
                    : ""
                }

                ${this.has_multiple_choice_question_part
                    ? x`
                        <h3 class="govuk-heading-s govuk-!-margin-bottom-2">
                            Response to multiple choice
                        </h3>
                        <p class="govuk-body answer">
                            ${this.multiple_choice_answer.length > 0
                                ? this.multiple_choice_answer.join(", ")
                                : "Not answered"
                            }
                        </p>
                    `
                    : ""
                }

                ${this.demographic_data && this.demographic_data.length > 0
                    ? x`
                        <div class="govuk-body-s demographic-data">
                            <h3>Demographic Data</h3>
                            <ul>
                                ${Object.keys(this.demographic_data).map(key => x`
                                    <li>
                                        ${key.slice(0, 1).toLocaleUpperCase()
                                            + key.slice(1)}: ${this.demographic_data[key]
                                        }
                                    </li>
                                `)}
                            </ul>
                        </div>
                    `
                    : ""
                }
            </div>
        `;
    }
}
customElements.define("iai-response", IaiResponse);

class IaiResponseFilterGroup extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._SLOT_NAMES = ["content"];
        
        // Prop defaults
        this.title = "";
        
        this.applyStaticStyles("iai-response-filter-group", IaiResponseFilterGroup.styles);
    }

    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return x`
            <div class="govuk-form-group">
                <fieldset class="govuk-fieldset">
                    <legend class="govuk-fieldset__legend govuk-fieldset__legend--m">
                        ${this.title}
                    </legend>

                    <slot name="content"></slot>

                </fieldset>
            </div>      
        `;
    }
}
customElements.define("iai-response-filter-group", IaiResponseFilterGroup);

class IaiQuestionTopbar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5em;
                background: white;
                border-radius: var(--iai-border-radius);
            }
            iai-question-topbar .question-title {
                color: var(--iai-colour-pink);
                margin: 0;
                font-size: 1rem;
            }

            @media only screen and (max-width: 1000px) {
                iai-question-topbar {
                    flex-direction: column-reverse;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._SLOT_NAMES = ["buttons"];

        // Prop defaults
        this.title = "";
        
        this.applyStaticStyles("iai-question-topbar", IaiQuestionTopbar.styles);
    }
    
    updated() {
        this._SLOT_NAMES.forEach(slotName => this.applySlots(slotName));
    }

    render() {
        return x`
            <h3 class="govuk-heading-m question-title">
                ${this.title}
            </h3>

            <slot name="buttons"></slot>
        `;
    }
}
customElements.define("iai-question-topbar", IaiQuestionTopbar);

class IaiQuestionBody extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: { type: String },
        searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-body p {
                line-height: 1.5em;
                font-size: 1.1em;
                margin-block: 0;
                min-height: 6em;
            }
            iai-question-body .matched-text {
                background-color: var(--iai-colour-focus);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "";
        this.searchValue = "";
        
        this.applyStaticStyles("iai-question-body", IaiQuestionBody.styles);
    }

    getHighlightedText = (fullText, matchedText) => {
        const regex = new RegExp(matchedText, "gi");
        return o$2(fullText.replace(regex, match => `<span class="matched-text">${match}</span>`));
    }
    
    render() {
        return x`
            <p>${this.getHighlightedText(this.text, this.searchValue)}</p>
        `;
    }
}
customElements.define("iai-question-body", IaiQuestionBody);

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

class IaiQuestionTile extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        _favourited: { type: Boolean },
        questionId: { type: String },
        title: { type: String },
        body: { type: String },
        maxLength: { type: Number },
        highlighted: { type: Boolean },
        searchValue: { type: String },
        handleViewClick: { type: Function },
        handleBodyClick: { type: Function },
        handleFavouriteClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-tile {
                width: 31%;
            }
            iai-question-tile .question-tile {
                height: 100%;    
                background: white;
                padding: 1em;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
                border: 2px solid transparent;
                transition: 0.3s ease-in-out;
                transition-property: border-color;
            }
            iai-question-tile .question-tile:hover,
            iai-question-tile .question-tile.highlighted {
                border: 2px solid var(--iai-colour-pink);
            }
            iai-question-tile div[slot="buttons"] {
                display: flex;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._STORAGE_KEY = "favouriteQuestions";

        // Prop defaults
        this._favourited = false;
        this.questionId = "";
        this.title = "";
        this.body = "";
        this.maxLength = 90;
        this.highlighted = false;
        this.searchValue = "";
        this.handleViewClick = () => {};
        this.handleBodyClick = () => {};
        this.handleFavouriteClick = this.handleFavouriteClick_;

        this.applyStaticStyles("iai-question-tile", IaiQuestionTile.styles);
    }

    getTruncatedText = (text, maxLength) => {
        return text.slice(0, maxLength) + (text.length > maxLength ? "..." : "");
    }

    firstUpdated() {
        this._favourited = this.getStoredIds().includes(this.questionId);
    }

    handleFavouriteClick_ = (e) => {
        e.stopPropagation();

        this.toggleStorage();

        this._favourited = this.getStoredIds().includes(this.questionId);
    }

    getStoredIds = () => {
        const storedValue = localStorage.getItem(this._STORAGE_KEY);
        return storedValue ? JSON.parse(storedValue) : [];
    }

    toggleStorage = () => {
        let questionIds = this.getStoredIds();

        if (questionIds.includes(this.questionId)) {
            questionIds = questionIds.filter(questionId => questionId != this.questionId);
        } else {
            questionIds.push(this.questionId);
        }
        localStorage.setItem(this._STORAGE_KEY, JSON.stringify(questionIds));
    }

    render() {
        return x`
            <div
                class=${"question-tile" + (this.highlighted ? " highlighted" : "")}
                role="button"
                tabindex="0"
                @click=${this.handleBodyClick}
                @keydown=${(e) => {
                    e.stopPropagation();

                    if (e.repeat) {
                        return;
                    }

                    if (this.accessibleKeyPressed(e.key)) {
                        this.handleBodyClick(e);
                    }
                }}
            >
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <iai-icon-button
                            title="View question details"
                            .handleClick=${(e) => {
                                e.stopPropagation();
                                this.handleViewClick(e);
                            }}
                            @keydown=${(e) => e.stopPropagation()}
                        >
                            <iai-icon
                                slot="icon"
                                name="visibility"
                                .color=${"var(--iai-colour-text-secondary)"}
                                .fill=${0}
                            ></iai-icon>
                        </iai-icon-button>

                        <iai-icon-button
                            title="Favourite this question"
                            .handleClick=${(e) => {
                                e.stopPropagation();
                                this.handleFavouriteClick(e);
                            }}
                            @keydown=${(e) => e.stopPropagation()}
                        >    
                            <iai-icon
                                slot="icon"
                                name="star"
                                .fill=${this._favourited ? 1 : 0}
                                .color= ${this._favourited
                                    ? "var(--iai-colour-pink)"
                                    : "var(--iai-colour-text-secondary)"
                                }
                            ></iai-icon>
                        </iai-icon-button>
                    </div>
                </iai-question-topbar>
                
                <iai-question-body
                    .text=${this.getTruncatedText(this.body, this.maxLength)}
                    .searchValue=${this.searchValue}
                ></iai-question-body>
            </div>
        `;
    }
}
customElements.define("iai-question-tile", IaiQuestionTile);

class IaiQuestionOverviewSubtitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        total: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-overview-subtitle {
                display:flex;
                justify-content: space-between;
                align-items: center;
            }
            iai-question-overview-subtitle .total {
                font-size: 1.1em;
            }
            iai-question-overview-subtitle h3 {
                font-size: 0.9em;
                color: var(--iai-colour-secondary);
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.total = 0;
        
        this.applyStaticStyles("iai-question-overview-subtitle", IaiQuestionOverviewSubtitle.styles);
    }

    render() {
        return x`
            <h3>
                ${this.title}
            </h3>
            <div class="total">
                Total: <strong>${this.total}</strong>
            </div>
        `;
    }
}
customElements.define("iai-question-overview-subtitle", IaiQuestionOverviewSubtitle);

class IaiTextResponseItem extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        iconName: { type: String },
        text: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-text-response-item p {
                margin: 0;
            }
            iai-text-response-item li {
                display: flex;
                justify-content: flex-start;
                align-items: center;
                gap: 1em;
            }
            iai-text-response-item li {
                margin-bottom: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.iconName = "";
        this.text = "";

        this.applyStaticStyles("iai-text-response-item", IaiTextResponseItem.styles);
    }

    render() {
        return x`
            <li>
                <iai-icon
                    name="${this.iconName}"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>
                <p>
                    ${this.text}
                </p>
            </li>
        `;
    }
}
customElements.define("iai-text-response-item", IaiTextResponseItem);

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

class IaiMultiResponseItem extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        countName: { type: String },
        countValue: { type: Number },
        totalCounts: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-multi-response-item p {
                margin: 0;
            }
            iai-multi-response-item progress {
                width: 100%;
            }
            iai-multi-response-item progress {
                accent-color: var(--iai-colour-pink);
            }
            iai-multi-response-item li {
                margin-bottom: 0.5em;
                list-style: none;
            }
            iai-multi-response-item iai-progress-bar .container .bar {
                height: 1.3em;
            }
            iai-multi-response-item iai-progress-bar .container .label,
            iai-multi-response-item iai-progress-bar .container.low-value .label {
                font-size: 0.9em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.key = "";
        this.count = 0;
        this.totalCounts = 0;

        this.applyStaticStyles("iai-multi-response-item", IaiMultiResponseItem.styles);
    }

    getPercentage = (part, whole) => {
        if (part === 0){
            return 0;
        }
        return Math.round((part / whole) * 100);
    }

    render() {
        return x`
            <li>
                <p>
                    ${this.countName ? this.countName + ": " : ""}<strong>${this.countValue}</strong>
                </p>
                <iai-progress-bar
                    .value=${this.getPercentage(this.countValue, this.totalCounts)}
                    .label=${this.getPercentage(this.countValue, this.totalCounts) + "%"}
                ></iai-progress-bar>
            </li>
        `;
    }
}
customElements.define("iai-multi-response-item", IaiMultiResponseItem);

class IaiQuestionOverview extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        body: { type: String },
        responses: { type: Object }, //  agreement | unclear | disagreement
        multiResponses: { type: Object },
        handleClose: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-overview .question-overview {
                background: white;
                padding: 1em;
                border-radius: var(--iai-border-radius);
            }
            iai-question-overview .multi-response-list {
                padding: 0;
                margin: 0;
                margin-top: 0.5em;
                list-style: none;
            }
            iai-question-overview .text-response-list {
                padding: 0;
                margin: 0;
                margin-top: 1em;
            }
            iai-question-overview hr {
                margin-block: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.body = "";
        this.responses = {};
        this.multiResponses = {};
        this.handleClose = () => {};

        this.applyStaticStyles("iai-question-overview", IaiQuestionOverview.styles);
    }

    getTextResponseTotal = () => {
        return this.responses.count || 0;
    }

    getMultiResponseTotal = () => {
        return Object.values(this.multiResponses).reduce((acc, curr) => acc + curr, 0);
    }

    renderCountFallback = () => {
      if (!this.responses.count) {
        return x`<p class="govuk-body">This question does not have free text responses</p>`
      }
    }

    render() {
        const textResponseTotal = this.getTextResponseTotal();
        const multiResponseTotal = this.getMultiResponseTotal();

        return x`
            <div class="question-overview">
                <iai-question-topbar .title=${this.title}>
                    <div slot="buttons">
                        <iai-icon-button
                            title="Close question overview"
                            .handleClick=${this.handleClose}
                        >
                            <iai-icon
                                slot="icon"
                                name="close"
                                .color=${"var(--iai-colour-text-secondary)"}
                            ></iai-icon>
                        </iai-icon-button>
                    </div>
                </iai-question-topbar>

                <iai-question-body
                    .text=${this.body}
                ></iai-question-body>

                <hr />

                <iai-question-overview-subtitle
                    title="Free Text Responses"
                    .total=${textResponseTotal}
                ></iai-question-overview-subtitle>

              ${this.renderCountFallback()}

                <hr />

                <iai-question-overview-subtitle
                    title="Multi-Choice Responses"
                    .total=${multiResponseTotal}
                ></iai-question-overview-subtitle>

                ${!this.multiResponses || !Object.keys(this.multiResponses).length > 0
                    ? x`<p class="govuk-body">This question does not have multiple choice responses</p>`
                    : x`
                        <ul class="multi-response-list">
                            ${Object.keys(this.multiResponses).map(key => x`
                                <iai-multi-response-item
                                    .countName=${key}
                                    .countValue=${this.multiResponses[key]}
                                    .totalCounts=${multiResponseTotal}
                                ></iai-multi-response-item>

                            `)}
                        </ul>
                    `
                }
            </div>
        `;
    }
}
customElements.define("iai-question-overview", IaiQuestionOverview);

class IaiTextInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
        hideLabel: {type: Boolean},
        placeholder: { type: String },
        value: { type: String },
        handleInput: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4``
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.hideLabel = false;
        this.placeholder = "";
        this.value = "";
        this.handleChange = () => {};

        this.applyStaticStyles("iai-text-input", IaiTextInput.styles);
    }

    render() {
        return x`
            <label
                for=${this.inputId}
                class=${
                    "govuk-label govuk-label--m"
                    + (this.hideLabel ? " visually-hidden" : "")
                }
            >
                ${this.label}
            </label>
            <input
                type="text"
                class="govuk-input"
                id=${this.inputId}
                name=${this.name}
                placeholder=${this.placeholder}
                value=${this.value}
                @input=${this.handleInput}
            />
        `
    }
}
customElements.define("iai-text-input", IaiTextInput);

class IaiQuestionTiles extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        consultationName: { type: String },
        questions: { type: Array },
        _visibleQuestions: { type: Array },
        _selectedQuestion: { type: Object },
        _searchValue: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-tiles iai-icon .material-symbols-outlined {
                font-size: 2em;
            }
            iai-question-tiles .questions {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-question-tiles .tile-panel {
                padding-right: 0;
            }
            iai-question-tiles .overview-panel {
                padding-left: 0;
            }
            iai-question-tiles .search-container {
                margin-bottom: 1em;
            }
            iai-question-tiles .search-container label {
                display: flex;
                align-items: center;
                margin-bottom: 0.5em;
                font-weight: normal;
                font-size: 1em;
                line-height: 0;
            }
            iai-question-tiles .search-container label iai-icon {
                margin-right: 0.5em;
            }
            iai-question-tiles .questions {
                max-height: 80vh;
                overflow: auto;
            }
            @media only screen and (max-width: 770px) {
                iai-question-tiles .overview-panel {
                    padding: 1em;
                    padding-top: 2em;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.consultationName = "";
        this.questions = [];
        this._visibleQuestions = [];
        this._selectedQuestion = null;
        this._searchValue = "";

        this.applyStaticStyles("iai-question-tiles", IaiQuestionTiles.styles);
    }

    firstUpdated() {
        if (this.questions.length > 0) {
            this._selectedQuestion = this.questions[0];
        }
    }

    updated(changedProps) {
        if (changedProps.has("_searchValue")) {
            this._visibleQuestions = this.questions.filter(
                question => this.searchMatches(question)
            );
        }
    }

    searchMatches = (question) => {
        if (!this._searchValue) {
            return true;
        }
        return (
            question.title.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()) ||
            question.body.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())
        )
    }

    handleViewClick = (e, question) => {
        e.stopPropagation();

        this._selectedQuestion = question;
    }

    handleTileClick = (e, url) => {
        window.location.href = url;
    }

    render() {
        return x`
            <iai-page-title
                title="All Questions"
                .subtitle=${this.consultationName}
            ></iai-page-title>

            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-three-quarters-from-desktop tile-panel">
                    <div class="questions">
                        ${this._visibleQuestions.length > 0
                            ? this._visibleQuestions.map(question => x`
                                <iai-question-tile
                                    .questionId=${question.id}
                                    .title=${question.title}
                                    .body=${question.body}
                                    .highlighted=${this._selectedQuestion == question}
                                    .searchValue=${this._searchValue}
                                    .handleViewClick=${(e) => this.handleViewClick(e, question)}
                                    .handleBodyClick=${(e) => this.handleTileClick(e, question.url)}
                                ></iai-question-tile>
                            `)
                            : x`<p>No matching question found.</p>`
                        }
                    </div>
                </div>

                <div class="govuk-grid-column-one-quarter-from-desktop overview-panel">
                    <div class="search-container">
                        <iai-text-input
                            inputId="question-search"  
                            name="question-search"
                            .label=${x`
                                <iai-icon
                                    slot="icon"
                                    name="search"
                                    .color=${"var(--iai-colour-text-secondary)"}
                                    .fill=${0}
                                ></iai-icon>
                                Search
                            `}
                            placeholder=${"Search..."}
                            value=${this._searchValue}
                            .handleInput=${(e) => this._searchValue = e.target.value.trim()}
                            .hideLabel=${false}
                        ></iai-text-input>
                    </div>
                    
                    ${this._selectedQuestion ? x`
                        <iai-question-overview
                            .title=${this._selectedQuestion.title}
                            .body=${this._selectedQuestion.body}
                            .responses=${this._selectedQuestion.responses}
                            .multiResponses=${this._selectedQuestion.multiResponses}
                            .handleClose=${() => this._selectedQuestion = null}
                        ></iai-question-overview>
                    ` : ""}
                </div>
            </div>
        `;
    }
}
customElements.define("iai-question-tiles", IaiQuestionTiles);

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

class IaiChip extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        label: {type: String},
        handleClick: {type: Function},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-chip {
                font-size: 0.9em;
            }
            
            iai-chip div {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1em;
                padding: 0.5em 1em;
                font-size: 1em;
                line-height: 1.5em;
                color: black;
                background: var(--iai-colour-pink-transparent-mid);
                border: none;
                border-radius: var(--iai-border-radius);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.label = "";
        this.handleClick = () => {};

        this.applyStaticStyles("iai-chip", IaiChip.styles);
    }

    render() {
        return x`    
            <div>
                <span>
                    ${this.label}
                </span>

                <iai-icon-button
                    title="Remove theme filter"
                    .handleClick=${this.handleClick}
                >
                    <iai-icon
                        slot="icon"
                        name="close"
                        .opsz=${12}
                        .color=${"black"}
                    ></iai-icon>
                </iai-icon-button>
            </div>
        `;
    }
}
customElements.define("iai-chip", IaiChip);

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

/******************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */
/* global Reflect, Promise, SuppressedError, Symbol, Iterator */


function __decorate(decorators, target, key, desc) {
  var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
  if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
  else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
  return c > 3 && r && Object.defineProperty(target, key, r), r;
}

typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
  var e = new Error(message);
  return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const o$1={attribute:true,type:String,converter:u$3,reflect:false,hasChanged:f$3},r$2=(t=o$1,e,r)=>{const{kind:n,metadata:i}=r;let s=globalThis.litPropertyMetadata.get(i);if(void 0===s&&globalThis.litPropertyMetadata.set(i,s=new Map),"setter"===n&&((t=Object.create(t)).wrapped=true),s.set(r.name,t),"accessor"===n){const{name:o}=r;return {set(r){const n=e.get.call(this);e.set.call(this,r),this.requestUpdate(o,n,t);},init(e){return void 0!==e&&this.C(o,void 0,t,e),e}}}if("setter"===n){const{name:o}=r;return function(r){const n=this[o];e.call(this,r),this.requestUpdate(o,n,t);}}throw Error("Unsupported decorator location: "+n)};function n$1(t){return (e,o)=>"object"==typeof o?r$2(t,e,o):((t,e,o)=>{const r=e.hasOwnProperty(o);return e.constructor.createProperty(o,t),r?Object.getOwnPropertyDescriptor(e,o):void 0})(t,e,o)}

/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const {I:t}=Z,f$1=o=>void 0===o.strings,s$1=()=>document.createComment(""),r$1=(o,i,n)=>{const e=o._$AA.parentNode,l=void 0===i?o._$AB:i._$AA;if(void 0===n){const i=e.insertBefore(s$1(),l),c=e.insertBefore(s$1(),l);n=new t(i,c,o,o.options);}else {const t=n._$AB.nextSibling,i=n._$AM,c=i!==o;if(c){let t;n._$AQ?.(o),n._$AM=o,void 0!==n._$AP&&(t=o._$AU)!==i._$AU&&n._$AP(t);}if(t!==l||c){let o=n._$AA;for(;o!==t;){const t=o.nextSibling;e.insertBefore(o,l),o=t;}}}return n},v=(o,t,i=o)=>(o._$AI(t,i),o),u$1={},m=(o,t=u$1)=>o._$AH=t,p=o=>o._$AH,M=o=>{o._$AP?.(false,true);let t=o._$AA;const i=o._$AB.nextSibling;for(;t!==i;){const o=t.nextSibling;t.remove(),t=o;}};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const s=(i,t)=>{const e=i._$AN;if(void 0===e)return  false;for(const i of e)i._$AO?.(t,false),s(i,t);return  true},o=i=>{let t,e;do{if(void 0===(t=i._$AM))break;e=t._$AN,e.delete(i),i=t;}while(0===e?.size)},r=i=>{for(let t;t=i._$AM;i=t){let e=t._$AN;if(void 0===e)t._$AN=e=new Set;else if(e.has(i))break;e.add(i),c$1(t);}};function h(i){ void 0!==this._$AN?(o(this),this._$AM=i,r(this)):this._$AM=i;}function n(i,t=false,e=0){const r=this._$AH,h=this._$AN;if(void 0!==h&&0!==h.size)if(t)if(Array.isArray(r))for(let i=e;i<r.length;i++)s(r[i],false),o(r[i]);else null!=r&&(s(r,false),o(r));else s(this,i);}const c$1=i=>{i.type==t$1.CHILD&&(i._$AP??=n,i._$AQ??=h);};class f extends i{constructor(){super(...arguments),this._$AN=void 0;}_$AT(i,t,e){super._$AT(i,t,e),r(this),this.isConnected=i._$AU;}_$AO(i,t=true){i!==this.isConnected&&(this.isConnected=i,i?this.reconnected?.():this.disconnected?.()),t&&(s(this,i),o(this));}setValue(t){if(f$1(this._$Ct))this._$Ct._$AI(t,this);else {const i=[...this._$Ct._$AH];i[this._$Ci]=t,this._$Ct._$AI(i,this,0);}}disconnected(){}reconnected(){}}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const u=(e,s,t)=>{const r=new Map;for(let l=s;l<=t;l++)r.set(e[l],l);return r},c=e$1(class extends i{constructor(e){if(super(e),e.type!==t$1.CHILD)throw Error("repeat() can only be used in text expressions")}dt(e,s,t){let r;void 0===t?t=s:void 0!==s&&(r=s);const l=[],o=[];let i=0;for(const s of e)l[i]=r?r(s,i):i,o[i]=t(s,i),i++;return {values:o,keys:l}}render(e,s,t){return this.dt(e,s,t).values}update(s,[t,r,c]){const d=p(s),{values:p$1,keys:a}=this.dt(t,r,c);if(!Array.isArray(d))return this.ut=a,p$1;const h=this.ut??=[],v$1=[];let m$1,y,x=0,j=d.length-1,k=0,w=p$1.length-1;for(;x<=j&&k<=w;)if(null===d[x])x++;else if(null===d[j])j--;else if(h[x]===a[k])v$1[k]=v(d[x],p$1[k]),x++,k++;else if(h[j]===a[w])v$1[w]=v(d[j],p$1[w]),j--,w--;else if(h[x]===a[w])v$1[w]=v(d[x],p$1[w]),r$1(s,v$1[w+1],d[x]),x++,w--;else if(h[j]===a[k])v$1[k]=v(d[j],p$1[k]),r$1(s,d[x],d[j]),j--,k++;else if(void 0===m$1&&(m$1=u(a,k,w),y=u(h,x,j)),m$1.has(h[x]))if(m$1.has(h[j])){const e=y.get(a[k]),t=void 0!==e?d[e]:null;if(null===t){const e=r$1(s,d[x]);v(e,p$1[k]),v$1[k]=e;}else v$1[k]=v(t,p$1[k]),r$1(s,d[x],t),d[e]=null;k++;}else M(d[j]),j--;else M(d[x]),x++;for(;k<=w;){const e=r$1(s,v$1[w+1]);v(e,p$1[k]),v$1[k++]=e;}for(;x<=j;){const e=d[x++];null!==e&&M(e);}return this.ut=a,m(s,v$1),T}});

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class RangeChangedEvent extends Event {
    constructor(range) {
        super(RangeChangedEvent.eventName, { bubbles: false });
        this.first = range.first;
        this.last = range.last;
    }
}
RangeChangedEvent.eventName = 'rangeChanged';
class VisibilityChangedEvent extends Event {
    constructor(range) {
        super(VisibilityChangedEvent.eventName, { bubbles: false });
        this.first = range.first;
        this.last = range.last;
    }
}
VisibilityChangedEvent.eventName = 'visibilityChanged';
class UnpinnedEvent extends Event {
    constructor() {
        super(UnpinnedEvent.eventName, { bubbles: false });
    }
}
UnpinnedEvent.eventName = 'unpinned';

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class ScrollerShim {
    constructor(element) {
        this._element = null;
        const node = element ?? window;
        this._node = node;
        if (element) {
            this._element = element;
        }
    }
    get element() {
        return (this._element || document.scrollingElement || document.documentElement);
    }
    get scrollTop() {
        return this.element.scrollTop || window.scrollY;
    }
    get scrollLeft() {
        return this.element.scrollLeft || window.scrollX;
    }
    get scrollHeight() {
        return this.element.scrollHeight;
    }
    get scrollWidth() {
        return this.element.scrollWidth;
    }
    get viewportHeight() {
        return this._element
            ? this._element.getBoundingClientRect().height
            : window.innerHeight;
    }
    get viewportWidth() {
        return this._element
            ? this._element.getBoundingClientRect().width
            : window.innerWidth;
    }
    get maxScrollTop() {
        return this.scrollHeight - this.viewportHeight;
    }
    get maxScrollLeft() {
        return this.scrollWidth - this.viewportWidth;
    }
}
class ScrollerController extends ScrollerShim {
    constructor(client, element) {
        super(element);
        this._clients = new Set();
        this._retarget = null;
        this._end = null;
        this.__destination = null;
        this.correctingScrollError = false;
        this._checkForArrival = this._checkForArrival.bind(this);
        this._updateManagedScrollTo = this._updateManagedScrollTo.bind(this);
        this.scrollTo = this.scrollTo.bind(this);
        this.scrollBy = this.scrollBy.bind(this);
        const node = this._node;
        this._originalScrollTo = node.scrollTo;
        this._originalScrollBy = node.scrollBy;
        this._originalScroll = node.scroll;
        this._attach(client);
    }
    get _destination() {
        return this.__destination;
    }
    get scrolling() {
        return this._destination !== null;
    }
    scrollTo(p1, p2) {
        const options = typeof p1 === 'number' && typeof p2 === 'number'
            ? { left: p1, top: p2 }
            : p1;
        this._scrollTo(options);
    }
    scrollBy(p1, p2) {
        const options = typeof p1 === 'number' && typeof p2 === 'number'
            ? { left: p1, top: p2 }
            : p1;
        if (options.top !== undefined) {
            options.top += this.scrollTop;
        }
        if (options.left !== undefined) {
            options.left += this.scrollLeft;
        }
        this._scrollTo(options);
    }
    _nativeScrollTo(options) {
        this._originalScrollTo.bind(this._element || window)(options);
    }
    _scrollTo(options, retarget = null, end = null) {
        if (this._end !== null) {
            this._end();
        }
        if (options.behavior === 'smooth') {
            this._setDestination(options);
            this._retarget = retarget;
            this._end = end;
        }
        else {
            this._resetScrollState();
        }
        this._nativeScrollTo(options);
    }
    _setDestination(options) {
        let { top, left } = options;
        top =
            top === undefined
                ? undefined
                : Math.max(0, Math.min(top, this.maxScrollTop));
        left =
            left === undefined
                ? undefined
                : Math.max(0, Math.min(left, this.maxScrollLeft));
        if (this._destination !== null &&
            left === this._destination.left &&
            top === this._destination.top) {
            return false;
        }
        this.__destination = { top, left, behavior: 'smooth' };
        return true;
    }
    _resetScrollState() {
        this.__destination = null;
        this._retarget = null;
        this._end = null;
    }
    _updateManagedScrollTo(coordinates) {
        if (this._destination) {
            if (this._setDestination(coordinates)) {
                this._nativeScrollTo(this._destination);
            }
        }
    }
    managedScrollTo(options, retarget, end) {
        this._scrollTo(options, retarget, end);
        return this._updateManagedScrollTo;
    }
    correctScrollError(coordinates) {
        this.correctingScrollError = true;
        requestAnimationFrame(() => requestAnimationFrame(() => (this.correctingScrollError = false)));
        // Correct the error
        this._nativeScrollTo(coordinates);
        // Then, if we were headed for a specific destination, we continue scrolling:
        // First, we update our target destination, if applicable...
        if (this._retarget) {
            this._setDestination(this._retarget());
        }
        // Then we go ahead and resume scrolling
        if (this._destination) {
            this._nativeScrollTo(this._destination);
        }
    }
    _checkForArrival() {
        if (this._destination !== null) {
            const { scrollTop, scrollLeft } = this;
            let { top, left } = this._destination;
            top = Math.min(top || 0, this.maxScrollTop);
            left = Math.min(left || 0, this.maxScrollLeft);
            const topDiff = Math.abs(top - scrollTop);
            const leftDiff = Math.abs(left - scrollLeft);
            // We check to see if we've arrived at our destination.
            if (topDiff < 1 && leftDiff < 1) {
                if (this._end) {
                    this._end();
                }
                this._resetScrollState();
            }
        }
    }
    detach(client) {
        this._clients.delete(client);
        /**
         * If there aren't any more clients, then return the node's default
         * scrolling methods
         */
        if (this._clients.size === 0) {
            this._node.scrollTo = this._originalScrollTo;
            this._node.scrollBy = this._originalScrollBy;
            this._node.scroll = this._originalScroll;
            this._node.removeEventListener('scroll', this._checkForArrival);
        }
        return null;
    }
    _attach(client) {
        this._clients.add(client);
        /**
         * The node should only have the methods shimmed when adding the first
         * client – otherwise it's redundant
         */
        if (this._clients.size === 1) {
            this._node.scrollTo = this.scrollTo;
            this._node.scrollBy = this.scrollBy;
            this._node.scroll = this.scrollTo;
            this._node.addEventListener('scroll', this._checkForArrival);
        }
    }
}

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
// Virtualizer depends on `ResizeObserver`, which is supported in
// all modern browsers. For developers whose browser support
// matrix includes older browsers, we include a compatible
// polyfill in the package; this bit of module state facilitates
// a simple mechanism (see ./polyfillLoaders/ResizeObserver.js.)
// for loading the polyfill.
let _ResizeObserver = typeof window !== 'undefined' ? window.ResizeObserver : undefined;
const virtualizerRef = Symbol('virtualizerRef');
const SIZER_ATTRIBUTE = 'virtualizer-sizer';
let DefaultLayoutConstructor;
/**
 * Provides virtual scrolling boilerplate.
 *
 * Extensions of this class must set hostElement and layout.
 *
 * Extensions of this class must also override VirtualRepeater's DOM
 * manipulation methods.
 */
class Virtualizer {
    constructor(config) {
        this._benchmarkStart = null;
        this._layout = null;
        this._clippingAncestors = [];
        /**
         * Layout provides these values, we set them on _render().
         * TODO @straversi: Can we find an XOR type, usable for the key here?
         */
        this._scrollSize = null;
        /**
         * Difference between scroll target's current and required scroll offsets.
         * Provided by layout.
         */
        this._scrollError = null;
        /**
         * A list of the positions (top, left) of the children in the current range.
         */
        this._childrenPos = null;
        // TODO: (graynorton): type
        this._childMeasurements = null;
        this._toBeMeasured = new Map();
        this._rangeChanged = true;
        this._itemsChanged = true;
        this._visibilityChanged = true;
        this._scrollerController = null;
        this._isScroller = false;
        this._sizer = null;
        /**
         * Resize observer attached to hostElement.
         */
        this._hostElementRO = null;
        /**
         * Resize observer attached to children.
         */
        this._childrenRO = null;
        this._mutationObserver = null;
        this._scrollEventListeners = [];
        this._scrollEventListenerOptions = {
            passive: true,
        };
        // TODO (graynorton): Rethink, per longer comment below
        this._loadListener = this._childLoaded.bind(this);
        /**
         * Index of element to scroll into view, plus scroll
         * behavior options, as imperatively specified via
         * `element(index).scrollIntoView()`
         */
        this._scrollIntoViewTarget = null;
        this._updateScrollIntoViewCoordinates = null;
        /**
         * Items to render. Set by items.
         */
        this._items = [];
        /**
         * Index of the first child in the range, not necessarily the first visible child.
         * TODO @straversi: Consider renaming these.
         */
        this._first = -1;
        /**
         * Index of the last child in the range.
         */
        this._last = -1;
        /**
         * Index of the first item intersecting the viewport.
         */
        this._firstVisible = -1;
        /**
         * Index of the last item intersecting the viewport.
         */
        this._lastVisible = -1;
        this._scheduled = new WeakSet();
        /**
         * Invoked at the end of each render cycle: children in the range are
         * measured, and their dimensions passed to this callback. Use it to layout
         * children as needed.
         */
        this._measureCallback = null;
        this._measureChildOverride = null;
        /**
         * State for `layoutComplete` promise
         */
        this._layoutCompletePromise = null;
        this._layoutCompleteResolver = null;
        this._layoutCompleteRejecter = null;
        this._pendingLayoutComplete = null;
        /**
         * Layout initialization is async because we dynamically load
         * the default layout if none is specified. This state is to track
         * whether init is complete.
         */
        this._layoutInitialized = null;
        /**
         * Track connection state to guard against errors / unnecessary work
         */
        this._connected = false;
        if (!config) {
            throw new Error('Virtualizer constructor requires a configuration object');
        }
        if (config.hostElement) {
            this._init(config);
        }
        else {
            throw new Error('Virtualizer configuration requires the "hostElement" property');
        }
    }
    set items(items) {
        if (Array.isArray(items) && items !== this._items) {
            this._itemsChanged = true;
            this._items = items;
            this._schedule(this._updateLayout);
        }
    }
    _init(config) {
        this._isScroller = !!config.scroller;
        this._initHostElement(config);
        // If no layout is specified, we make an empty
        // layout config, which will result in the default
        // layout with default parameters
        const layoutConfig = config.layout || {};
        // Save the promise returned by `_initLayout` as a state
        // variable we can check before updating layout config
        this._layoutInitialized = this._initLayout(layoutConfig);
    }
    _initObservers() {
        this._mutationObserver = new MutationObserver(this._finishDOMUpdate.bind(this));
        this._hostElementRO = new _ResizeObserver(() => this._hostElementSizeChanged());
        this._childrenRO = new _ResizeObserver(this._childrenSizeChanged.bind(this));
    }
    _initHostElement(config) {
        const hostElement = (this._hostElement = config.hostElement);
        this._applyVirtualizerStyles();
        hostElement[virtualizerRef] = this;
    }
    connected() {
        this._initObservers();
        const includeSelf = this._isScroller;
        this._clippingAncestors = getClippingAncestors(this._hostElement, includeSelf);
        this._scrollerController = new ScrollerController(this, this._clippingAncestors[0]);
        this._schedule(this._updateLayout);
        this._observeAndListen();
        this._connected = true;
    }
    _observeAndListen() {
        this._mutationObserver.observe(this._hostElement, { childList: true });
        this._hostElementRO.observe(this._hostElement);
        this._scrollEventListeners.push(window);
        window.addEventListener('scroll', this, this._scrollEventListenerOptions);
        this._clippingAncestors.forEach((ancestor) => {
            ancestor.addEventListener('scroll', this, this._scrollEventListenerOptions);
            this._scrollEventListeners.push(ancestor);
            this._hostElementRO.observe(ancestor);
        });
        this._hostElementRO.observe(this._scrollerController.element);
        this._children.forEach((child) => this._childrenRO.observe(child));
        this._scrollEventListeners.forEach((target) => target.addEventListener('scroll', this, this._scrollEventListenerOptions));
    }
    disconnected() {
        this._scrollEventListeners.forEach((target) => target.removeEventListener('scroll', this, this._scrollEventListenerOptions));
        this._scrollEventListeners = [];
        this._clippingAncestors = [];
        this._scrollerController?.detach(this);
        this._scrollerController = null;
        this._mutationObserver?.disconnect();
        this._mutationObserver = null;
        this._hostElementRO?.disconnect();
        this._hostElementRO = null;
        this._childrenRO?.disconnect();
        this._childrenRO = null;
        this._rejectLayoutCompletePromise('disconnected');
        this._connected = false;
    }
    _applyVirtualizerStyles() {
        const hostElement = this._hostElement;
        // Would rather set these CSS properties on the host using Shadow Root
        // style scoping (and falling back to a global stylesheet where native
        // Shadow DOM is not available), but this Mobile Safari bug is preventing
        // that from working: https://bugs.webkit.org/show_bug.cgi?id=226195
        const style = hostElement.style;
        style.display = style.display || 'block';
        style.position = style.position || 'relative';
        style.contain = style.contain || 'size layout';
        if (this._isScroller) {
            style.overflow = style.overflow || 'auto';
            style.minHeight = style.minHeight || '150px';
        }
    }
    _getSizer() {
        const hostElement = this._hostElement;
        if (!this._sizer) {
            // Use a preexisting sizer element if provided (for better integration
            // with vDOM renderers)
            let sizer = hostElement.querySelector(`[${SIZER_ATTRIBUTE}]`);
            if (!sizer) {
                sizer = document.createElement('div');
                sizer.setAttribute(SIZER_ATTRIBUTE, '');
                hostElement.appendChild(sizer);
            }
            // When the scrollHeight is large, the height of this element might be
            // ignored. Setting content and font-size ensures the element has a size.
            Object.assign(sizer.style, {
                position: 'absolute',
                margin: '-2px 0 0 0',
                padding: 0,
                visibility: 'hidden',
                fontSize: '2px',
            });
            sizer.textContent = '&nbsp;';
            sizer.setAttribute(SIZER_ATTRIBUTE, '');
            this._sizer = sizer;
        }
        return this._sizer;
    }
    async updateLayoutConfig(layoutConfig) {
        // If layout initialization hasn't finished yet, we wait
        // for it to finish so we can check whether the new config
        // is compatible with the existing layout before proceeding.
        await this._layoutInitialized;
        const Ctor = layoutConfig.type ||
            // The new config is compatible with the current layout,
            // so we update the config and return true to indicate
            // a successful update
            DefaultLayoutConstructor;
        if (typeof Ctor === 'function' && this._layout instanceof Ctor) {
            const config = { ...layoutConfig };
            delete config.type;
            this._layout.config = config;
            // The new config requires a different layout altogether, but
            // to limit implementation complexity we don't support dynamically
            // changing the layout of an existing virtualizer instance.
            // Returning false here lets the caller know that they should
            // instead make a new virtualizer instance with the desired layout.
            return true;
        }
        return false;
    }
    async _initLayout(layoutConfig) {
        let config;
        let Ctor;
        if (typeof layoutConfig.type === 'function') {
            // If we have a full LayoutSpecifier, the `type` property
            // gives us our constructor...
            Ctor = layoutConfig.type;
            // ...while the rest of the specifier is our layout config
            const copy = { ...layoutConfig };
            delete copy.type;
            config = copy;
        }
        else {
            // If we don't have a full LayoutSpecifier, we just
            // have a config for the default layout
            config = layoutConfig;
        }
        if (Ctor === undefined) {
            // If we don't have a constructor yet, load the default
            DefaultLayoutConstructor = Ctor = (await import('./flow-BYvW0t4Z.js'))
                .FlowLayout;
        }
        this._layout = new Ctor((message) => this._handleLayoutMessage(message), config);
        if (this._layout.measureChildren &&
            typeof this._layout.updateItemSizes === 'function') {
            if (typeof this._layout.measureChildren === 'function') {
                this._measureChildOverride = this._layout.measureChildren;
            }
            this._measureCallback = this._layout.updateItemSizes.bind(this._layout);
        }
        if (this._layout.listenForChildLoadEvents) {
            this._hostElement.addEventListener('load', this._loadListener, true);
        }
        this._schedule(this._updateLayout);
    }
    // TODO (graynorton): Rework benchmarking so that it has no API and
    // instead is always on except in production builds
    startBenchmarking() {
        if (this._benchmarkStart === null) {
            this._benchmarkStart = window.performance.now();
        }
    }
    stopBenchmarking() {
        if (this._benchmarkStart !== null) {
            const now = window.performance.now();
            const timeElapsed = now - this._benchmarkStart;
            const entries = performance.getEntriesByName('uv-virtualizing', 'measure');
            const virtualizationTime = entries
                .filter((e) => e.startTime >= this._benchmarkStart && e.startTime < now)
                .reduce((t, m) => t + m.duration, 0);
            this._benchmarkStart = null;
            return { timeElapsed, virtualizationTime };
        }
        return null;
    }
    _measureChildren() {
        const mm = {};
        const children = this._children;
        const fn = this._measureChildOverride || this._measureChild;
        for (let i = 0; i < children.length; i++) {
            const child = children[i];
            const idx = this._first + i;
            if (this._itemsChanged || this._toBeMeasured.has(child)) {
                mm[idx] = fn.call(this, child, this._items[idx]);
            }
        }
        this._childMeasurements = mm;
        this._schedule(this._updateLayout);
        this._toBeMeasured.clear();
    }
    /**
     * Returns the width, height, and margins of the given child.
     */
    _measureChild(element) {
        // offsetWidth doesn't take transforms in consideration, so we use
        // getBoundingClientRect which does.
        const { width, height } = element.getBoundingClientRect();
        return Object.assign({ width, height }, getMargins(element));
    }
    async _schedule(method) {
        if (!this._scheduled.has(method)) {
            this._scheduled.add(method);
            await Promise.resolve();
            this._scheduled.delete(method);
            method.call(this);
        }
    }
    async _updateDOM(state) {
        this._scrollSize = state.scrollSize;
        this._adjustRange(state.range);
        this._childrenPos = state.childPositions;
        this._scrollError = state.scrollError || null;
        const { _rangeChanged, _itemsChanged } = this;
        if (this._visibilityChanged) {
            this._notifyVisibility();
            this._visibilityChanged = false;
        }
        if (_rangeChanged || _itemsChanged) {
            this._notifyRange();
            this._rangeChanged = false;
        }
        this._finishDOMUpdate();
    }
    _finishDOMUpdate() {
        if (this._connected) {
            // _childrenRO should be non-null if we're connected
            this._children.forEach((child) => this._childrenRO.observe(child));
            this._checkScrollIntoViewTarget(this._childrenPos);
            this._positionChildren(this._childrenPos);
            this._sizeHostElement(this._scrollSize);
            this._correctScrollError();
            if (this._benchmarkStart && 'mark' in window.performance) {
                window.performance.mark('uv-end');
            }
        }
    }
    _updateLayout() {
        if (this._layout && this._connected) {
            this._layout.items = this._items;
            this._updateView();
            if (this._childMeasurements !== null) {
                // If the layout has been changed, we may have measurements but no callback
                if (this._measureCallback) {
                    this._measureCallback(this._childMeasurements);
                }
                this._childMeasurements = null;
            }
            this._layout.reflowIfNeeded();
            if (this._benchmarkStart && 'mark' in window.performance) {
                window.performance.mark('uv-end');
            }
        }
    }
    _handleScrollEvent() {
        if (this._benchmarkStart && 'mark' in window.performance) {
            try {
                window.performance.measure('uv-virtualizing', 'uv-start', 'uv-end');
            }
            catch (e) {
                console.warn('Error measuring performance data: ', e);
            }
            window.performance.mark('uv-start');
        }
        if (this._scrollerController.correctingScrollError === false) {
            // This is a user-initiated scroll, so we unpin the layout
            this._layout?.unpin();
        }
        this._schedule(this._updateLayout);
    }
    handleEvent(event) {
        switch (event.type) {
            case 'scroll':
                if (event.currentTarget === window ||
                    this._clippingAncestors.includes(event.currentTarget)) {
                    this._handleScrollEvent();
                }
                break;
            default:
                console.warn('event not handled', event);
        }
    }
    _handleLayoutMessage(message) {
        if (message.type === 'stateChanged') {
            this._updateDOM(message);
        }
        else if (message.type === 'visibilityChanged') {
            this._firstVisible = message.firstVisible;
            this._lastVisible = message.lastVisible;
            this._notifyVisibility();
        }
        else if (message.type === 'unpinned') {
            this._hostElement.dispatchEvent(new UnpinnedEvent());
        }
    }
    get _children() {
        const arr = [];
        let next = this._hostElement.firstElementChild;
        while (next) {
            if (!next.hasAttribute(SIZER_ATTRIBUTE)) {
                arr.push(next);
            }
            next = next.nextElementSibling;
        }
        return arr;
    }
    _updateView() {
        const hostElement = this._hostElement;
        const scrollingElement = this._scrollerController?.element;
        const layout = this._layout;
        if (hostElement && scrollingElement && layout) {
            let top, left, bottom, right;
            const hostElementBounds = hostElement.getBoundingClientRect();
            top = 0;
            left = 0;
            bottom = window.innerHeight;
            right = window.innerWidth;
            const ancestorBounds = this._clippingAncestors.map((ancestor) => ancestor.getBoundingClientRect());
            ancestorBounds.unshift(hostElementBounds);
            for (const bounds of ancestorBounds) {
                top = Math.max(top, bounds.top);
                left = Math.max(left, bounds.left);
                bottom = Math.min(bottom, bounds.bottom);
                right = Math.min(right, bounds.right);
            }
            const scrollingElementBounds = scrollingElement.getBoundingClientRect();
            const offsetWithinScroller = {
                left: hostElementBounds.left - scrollingElementBounds.left,
                top: hostElementBounds.top - scrollingElementBounds.top,
            };
            const totalScrollSize = {
                width: scrollingElement.scrollWidth,
                height: scrollingElement.scrollHeight,
            };
            const scrollTop = top - hostElementBounds.top + hostElement.scrollTop;
            const scrollLeft = left - hostElementBounds.left + hostElement.scrollLeft;
            const height = Math.max(0, bottom - top);
            const width = Math.max(0, right - left);
            layout.viewportSize = { width, height };
            layout.viewportScroll = { top: scrollTop, left: scrollLeft };
            layout.totalScrollSize = totalScrollSize;
            layout.offsetWithinScroller = offsetWithinScroller;
        }
    }
    /**
     * Styles the host element so that its size reflects the
     * total size of all items.
     */
    _sizeHostElement(size) {
        // Some browsers seem to crap out if the host element gets larger than
        // a certain size, so we clamp it here (this value based on ad hoc
        // testing in Chrome / Safari / Firefox Mac)
        const max = 8200000;
        const h = size && size.width !== null ? Math.min(max, size.width) : 0;
        const v = size && size.height !== null ? Math.min(max, size.height) : 0;
        if (this._isScroller) {
            this._getSizer().style.transform = `translate(${h}px, ${v}px)`;
        }
        else {
            const style = this._hostElement.style;
            style.minWidth = h ? `${h}px` : '100%';
            style.minHeight = v ? `${v}px` : '100%';
        }
    }
    /**
     * Sets the top and left transform style of the children from the values in
     * pos.
     */
    _positionChildren(pos) {
        if (pos) {
            pos.forEach(({ top, left, width, height, xOffset, yOffset }, index) => {
                const child = this._children[index - this._first];
                if (child) {
                    child.style.position = 'absolute';
                    child.style.boxSizing = 'border-box';
                    child.style.transform = `translate(${left}px, ${top}px)`;
                    if (width !== undefined) {
                        child.style.width = width + 'px';
                    }
                    if (height !== undefined) {
                        child.style.height = height + 'px';
                    }
                    child.style.left =
                        xOffset === undefined ? null : xOffset + 'px';
                    child.style.top =
                        yOffset === undefined ? null : yOffset + 'px';
                }
            });
        }
    }
    async _adjustRange(range) {
        const { _first, _last, _firstVisible, _lastVisible } = this;
        this._first = range.first;
        this._last = range.last;
        this._firstVisible = range.firstVisible;
        this._lastVisible = range.lastVisible;
        this._rangeChanged =
            this._rangeChanged || this._first !== _first || this._last !== _last;
        this._visibilityChanged =
            this._visibilityChanged ||
                this._firstVisible !== _firstVisible ||
                this._lastVisible !== _lastVisible;
    }
    _correctScrollError() {
        if (this._scrollError) {
            const { scrollTop, scrollLeft } = this._scrollerController;
            const { top, left } = this._scrollError;
            this._scrollError = null;
            this._scrollerController.correctScrollError({
                top: scrollTop - top,
                left: scrollLeft - left,
            });
        }
    }
    element(index) {
        if (index === Infinity) {
            index = this._items.length - 1;
        }
        return this._items?.[index] === undefined
            ? undefined
            : {
                scrollIntoView: (options = {}) => this._scrollElementIntoView({ ...options, index }),
            };
    }
    _scrollElementIntoView(options) {
        if (options.index >= this._first && options.index <= this._last) {
            this._children[options.index - this._first].scrollIntoView(options);
        }
        else {
            options.index = Math.min(options.index, this._items.length - 1);
            if (options.behavior === 'smooth') {
                const coordinates = this._layout.getScrollIntoViewCoordinates(options);
                const { behavior } = options;
                this._updateScrollIntoViewCoordinates =
                    this._scrollerController.managedScrollTo(Object.assign(coordinates, { behavior }), () => this._layout.getScrollIntoViewCoordinates(options), () => (this._scrollIntoViewTarget = null));
                this._scrollIntoViewTarget = options;
            }
            else {
                this._layout.pin = options;
            }
        }
    }
    /**
     * If we are smoothly scrolling to an element and the target element
     * is in the DOM, we update our target coordinates as needed
     */
    _checkScrollIntoViewTarget(pos) {
        const { index } = this._scrollIntoViewTarget || {};
        if (index && pos?.has(index)) {
            this._updateScrollIntoViewCoordinates(this._layout.getScrollIntoViewCoordinates(this._scrollIntoViewTarget));
        }
    }
    /**
     * Emits a rangechange event with the current first, last, firstVisible, and
     * lastVisible.
     */
    _notifyRange() {
        this._hostElement.dispatchEvent(new RangeChangedEvent({ first: this._first, last: this._last }));
    }
    _notifyVisibility() {
        this._hostElement.dispatchEvent(new VisibilityChangedEvent({
            first: this._firstVisible,
            last: this._lastVisible,
        }));
    }
    get layoutComplete() {
        // Lazily create promise
        if (!this._layoutCompletePromise) {
            this._layoutCompletePromise = new Promise((resolve, reject) => {
                this._layoutCompleteResolver = resolve;
                this._layoutCompleteRejecter = reject;
            });
        }
        return this._layoutCompletePromise;
    }
    _rejectLayoutCompletePromise(reason) {
        if (this._layoutCompleteRejecter !== null) {
            this._layoutCompleteRejecter(reason);
        }
        this._resetLayoutCompleteState();
    }
    _scheduleLayoutComplete() {
        // Don't do anything unless we have a pending promise
        // And only request a frame if we haven't already done so
        if (this._layoutCompletePromise && this._pendingLayoutComplete === null) {
            // Wait one additional frame to be sure the layout is stable
            this._pendingLayoutComplete = requestAnimationFrame(() => requestAnimationFrame(() => this._resolveLayoutCompletePromise()));
        }
    }
    _resolveLayoutCompletePromise() {
        if (this._layoutCompleteResolver !== null) {
            this._layoutCompleteResolver();
        }
        this._resetLayoutCompleteState();
    }
    _resetLayoutCompleteState() {
        this._layoutCompletePromise = null;
        this._layoutCompleteResolver = null;
        this._layoutCompleteRejecter = null;
        this._pendingLayoutComplete = null;
    }
    /**
     * Render and update the view at the next opportunity with the given
     * hostElement size.
     */
    _hostElementSizeChanged() {
        this._schedule(this._updateLayout);
    }
    // TODO (graynorton): Rethink how this works. Probably child loading is too specific
    // to have dedicated support for; might want some more generic lifecycle hooks for
    // layouts to use. Possibly handle measurement this way, too, or maybe that remains
    // a first-class feature?
    _childLoaded() { }
    // This is the callback for the ResizeObserver that watches the
    // virtualizer's children. We land here at the end of every virtualizer
    // update cycle that results in changes to physical items, and we also
    // end up here if one or more children change size independently of
    // the virtualizer update cycle.
    _childrenSizeChanged(changes) {
        // Only measure if the layout requires it
        if (this._layout?.measureChildren) {
            for (const change of changes) {
                this._toBeMeasured.set(change.target, change.contentRect);
            }
            this._measureChildren();
        }
        // If this is the end of an update cycle, we need to reset some
        // internal state. This should be a harmless no-op if we're handling
        // an out-of-cycle ResizeObserver callback, so we don't need to
        // distinguish between the two cases.
        this._scheduleLayoutComplete();
        this._itemsChanged = false;
        this._rangeChanged = false;
    }
}
function getMargins(el) {
    const style = window.getComputedStyle(el);
    return {
        marginTop: getMarginValue(style.marginTop),
        marginRight: getMarginValue(style.marginRight),
        marginBottom: getMarginValue(style.marginBottom),
        marginLeft: getMarginValue(style.marginLeft),
    };
}
function getMarginValue(value) {
    const float = value ? parseFloat(value) : NaN;
    return Number.isNaN(float) ? 0 : float;
}
// TODO (graynorton): Deal with iframes?
function getParentElement(el) {
    if (el.assignedSlot !== null) {
        return el.assignedSlot;
    }
    if (el.parentElement !== null) {
        return el.parentElement;
    }
    const parentNode = el.parentNode;
    if (parentNode && parentNode.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
        return parentNode.host || null;
    }
    return null;
}
///
function getElementAncestors(el, includeSelf = false) {
    const ancestors = [];
    let parent = includeSelf ? el : getParentElement(el);
    while (parent !== null) {
        ancestors.push(parent);
        parent = getParentElement(parent);
    }
    return ancestors;
}
function getClippingAncestors(el, includeSelf = false) {
    let foundFixed = false;
    return getElementAncestors(el, includeSelf).filter((a) => {
        if (foundFixed) {
            return false;
        }
        const style = getComputedStyle(a);
        foundFixed = style.position === 'fixed';
        return style.overflow !== 'visible';
    });
}

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const defaultKeyFunction = (item) => item;
const defaultRenderItem = (item, idx) => x `${idx}: ${JSON.stringify(item, null, 2)}`;
class VirtualizeDirective extends f {
    constructor(part) {
        super(part);
        this._virtualizer = null;
        this._first = 0;
        this._last = -1;
        this._renderItem = (item, idx) => defaultRenderItem(item, idx + this._first);
        this._keyFunction = (item, idx) => defaultKeyFunction(item, idx + this._first);
        this._items = [];
        if (part.type !== t$1.CHILD) {
            throw new Error('The virtualize directive can only be used in child expressions');
        }
    }
    render(config) {
        if (config) {
            this._setFunctions(config);
        }
        const itemsToRender = [];
        if (this._first >= 0 && this._last >= this._first) {
            for (let i = this._first; i <= this._last; i++) {
                itemsToRender.push(this._items[i]);
            }
        }
        return c(itemsToRender, this._keyFunction, this._renderItem);
    }
    update(part, [config]) {
        this._setFunctions(config);
        const itemsChanged = this._items !== config.items;
        this._items = config.items || [];
        if (this._virtualizer) {
            this._updateVirtualizerConfig(part, config);
        }
        else {
            this._initialize(part, config);
        }
        return itemsChanged ? T : this.render();
    }
    async _updateVirtualizerConfig(part, config) {
        const compatible = await this._virtualizer.updateLayoutConfig(config.layout || {});
        if (!compatible) {
            const hostElement = part.parentNode;
            this._makeVirtualizer(hostElement, config);
        }
        this._virtualizer.items = this._items;
    }
    _setFunctions(config) {
        const { renderItem, keyFunction } = config;
        if (renderItem) {
            this._renderItem = (item, idx) => renderItem(item, idx + this._first);
        }
        if (keyFunction) {
            this._keyFunction = (item, idx) => keyFunction(item, idx + this._first);
        }
    }
    _makeVirtualizer(hostElement, config) {
        if (this._virtualizer) {
            this._virtualizer.disconnected();
        }
        const { layout, scroller, items } = config;
        this._virtualizer = new Virtualizer({ hostElement, layout, scroller });
        this._virtualizer.items = items;
        this._virtualizer.connected();
    }
    _initialize(part, config) {
        const hostElement = part.parentNode;
        if (hostElement && hostElement.nodeType === 1) {
            hostElement.addEventListener('rangeChanged', (e) => {
                this._first = e.first;
                this._last = e.last;
                this.setValue(this.render());
            });
            this._makeVirtualizer(hostElement, config);
        }
    }
    disconnected() {
        this._virtualizer?.disconnected();
    }
    reconnected() {
        this._virtualizer?.connected();
    }
}
const virtualize = e$1(VirtualizeDirective);

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class LitVirtualizer extends i$1 {
    constructor() {
        super(...arguments);
        this.items = [];
        this.renderItem = defaultRenderItem;
        this.keyFunction = defaultKeyFunction;
        this.layout = {};
        this.scroller = false;
    }
    createRenderRoot() {
        return this;
    }
    render() {
        const { items, renderItem, keyFunction, layout, scroller } = this;
        return x `${virtualize({
            items,
            renderItem,
            keyFunction,
            layout,
            scroller,
        })}`;
    }
    element(index) {
        return this[virtualizerRef]?.element(index);
    }
    get layoutComplete() {
        return this[virtualizerRef]?.layoutComplete;
    }
    /**
     * This scrollToIndex() shim is here to provide backwards compatibility with other 0.x versions of
     * lit-virtualizer. It is deprecated and will likely be removed in the 1.0.0 release.
     */
    scrollToIndex(index, position = 'start') {
        this.element(index)?.scrollIntoView({ block: position });
    }
}
__decorate([
    n$1({ attribute: false })
], LitVirtualizer.prototype, "items", void 0);
__decorate([
    n$1()
], LitVirtualizer.prototype, "renderItem", void 0);
__decorate([
    n$1()
], LitVirtualizer.prototype, "keyFunction", void 0);
__decorate([
    n$1({ attribute: false })
], LitVirtualizer.prototype, "layout", void 0);
__decorate([
    n$1({ reflect: true, type: Boolean })
], LitVirtualizer.prototype, "scroller", void 0);

/**
 * @license
 * Copyright 2021 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
/**
 * Import this module to declare the lit-virtualizer custom element.
 */
customElements.define('lit-virtualizer', LitVirtualizer);

class IaiVirtualList extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: {type: Array},
        renderItem: {type: Function},
        handleScrollEnd: {type: Function},
        message: {type: String},
        _canCallCallback: {type: Boolean},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-virtual-list {
                display: block;
            }
            iai-virtual-list lit-virtualizer {
                height: 100%;
            }
            iai-virtual-list p.message {
                text-align: center;
                font-style: italic;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._CALLBACK_COOLDOWN = 2000;

        // Prop defaults
        this.data = [];
        this.renderItem = () => console.warn(
            "IaiVirtualList warning: renderResponse prop not passed"
        );
        this.handleScrollEnd = () => {};
        this.message = "";
        this._canCallCallback = true;
        
        this.applyStaticStyles("iai-virtual-list", IaiVirtualList.styles);
    }

    render() {
        if (this.message) {
            return x`<p class="message">${this.message}</p>`;
        }

        return x`
            <lit-virtualizer
                role="list"
                scroller
                .items=${this.data}
                .renderItem=${this.renderItem}
                @scroll=${() => {
                    const lastItem = document.querySelector(".last-item");

                    if (lastItem && this.handleScrollEnd && this._canCallCallback) {
                        this.handleScrollEnd();

                        this._canCallCallback = false;
                        setTimeout(
                            () => this._canCallCallback = true,
                            this._CALLBACK_COOLDOWN
                        );
                    }
                }}
            ></lit-virtualizer>
        `;
    }
}
customElements.define("iai-virtual-list", IaiVirtualList);

class IaiResponseDashboard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,

        consultationTitle: { type: String },
        consultationSlug: { type: String },
        questionTitle: { type: String },
        questionText: { type: String },
        questionSlug: { type: String },
        stanceOptions: { type: Array },
        themeMappings: { type: Array },
        demographicOptions: { type: Object },  // e.g. {"individual": ["true", "false"], "region": ["north", "south"]}
        responses: { type: Array },
        responsesTotal: { type: Number },
        free_text_question_part: { type: Boolean },
        has_multiple_choice_question_part: { type: Boolean },
        multiple_choice_summary: { type: Array },
        fetchData: { type: Function },

        _isLoading: { type: Boolean },
        _searchValue: { type: String },
        _themeSearchValue: { type: String },
        _demographicFilters: { type: Object },  // Changed from Array to Object to store filters by field
        _themeFilters: { type: Array },
        _themesPanelVisible: { type: Boolean },
        _stanceFilters: { type: Array },
        _responsesFilteredTotal: { type: Number },
        _evidenceRichFilters: { type: Array },
        _numberAnimationDuration: { type: Number },
        _searchDebounceTimer: { type: Number },
        _currentPage: { type: Number },
        _hasMorePages: { type: Boolean },
        _errorOccured: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-response-dashboard {
                margin-bottom: 5em;
            }
            .themes-container {
                position: relative;
            }
            .themes-panel {
                position: absolute;
                opacity: 0;
                transition: 0.3s;
                background-color: white;
                z-index: 1;
                width: 100%;
                top: 100%;
                max-height: 30vh;
                left: 0;
                box-shadow: rgba(100, 100, 111, 0.2) 0px 7px 29px 0px;
                padding: 1em;
                overflow: auto;
                pointer-events: none;
            }
            .themes-panel.visible {
                opacity: 1;
                pointer-events: auto;
            }
            .count-display {
                border: 2px solid var(--iai-colour-secondary);
                padding: 0.25em 0.75em;
                background: var(--iai-colour-secondary-transparent);
            }
            iai-response-dashboard .question-text {
                margin-top: 2em;
                font-size: 1.4em;
            }
            iai-response-dashboard hr {
                margin-bottom: 2em;
            }
            iai-response-dashboard .responses-column {
                display: flex;
                flex-direction: column;
                background: white;
                padding: 1em 2em;
                width: 73.5%;
            }
            iai-response-dashboard .responses-column .title-container {
                display: flex;
                justify-content:space-between;
                align-items: center;
                row-gap: 1em;
                padding-block: 1em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .responses-column .title-container>*:first-child,
            iai-response-dashboard .responses-column .title-container>*:last-child {
                flex-grow: 1;
            }
            iai-response-dashboard .responses-column .title-container h2 {
                margin: 0;
            }
            iai-response-dashboard .filters-column {
                padding-right: 1.5em;
            }
            iai-response-dashboard .theme-filters-applied {
                margin-bottom: 1em;
            }
            iai-response-dashboard .theme-filters-applied ul {
                list-style: none;
                padding: 0;
                display: flex;
                gap: 1em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .table-container {
                background: white;
                padding: 2em;
            }
            iai-response-dashboard .table-title {
                display: flex;
                justify-content: space-between;
                margin-bottom: 2em;
            }
            iai-response-dashboard .table-title.themes-mentions {
                margin-bottom: 0;
            }
            iai-response-dashboard .themes-mentions iai-csv-download a {
                margin-bottom: 0;
            }
            iai-response-dashboard .table-title h2 {
                margin: 0;
            }
            iai-response-dashboard .themes-container .input-container {
                position: relative;
            }
            iai-response-dashboard .table-container iai-data-table {
                display: block;
                max-height: 40em;
                overflow: auto;
            }
            iai-response-dashboard thead tr {
                color: var(--iai-colour-text-secondary);
            }
            iai-response-dashboard table iai-expanding-pill button {
                display: flex;
                justify-content: space-between;
                width: 100%;
                font-size: 1.2em;
                color: black;
                background: var(--iai-colour-pink-transparent-mid);
            }
            iai-response-dashboard table iai-expanding-pill .body {
                font-size: 1.2em;
                transition-property: margin, padding, max-height;
            }
            iai-response-dashboard table iai-expanding-pill .body:not(.expanded) {
                margin: 0;
            }
            iai-response-dashboard table .percentage-cell {
                display: flex;
                gap: 0.2em;
                min-width: 4.5em;
                font-size: 2em;
                font-weight: bold;
                color: var(--iai-colour-text-secondary);
            }
            iai-response-dashboard table .total-count-cell {
                min-width: 10em;
            }
            iai-response-dashboard .title-container {
                display: flex;
                align-items: center;
                row-gap: 0;
                column-gap: 2em;
                flex-wrap: wrap;
            }
            iai-response-dashboard .ternary-button {
                background: none;
                border: none;
                border-radius: var(--iai-border-radius);
                cursor: pointer;
                transition: color 0.3s ease-in-out;
                padding: 0;
                text-align: start;
            }
            iai-response-dashboard .ternary-button:hover {
                color: var(--iai-colour-pink);
            }
            iai-response-dashboard .responses-row {
                display: flex;
                min-height: 90vh;
            }
            iai-response-dashboard .flex-grow {
                flex-grow: 1;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this._PAGE_SIZE = 50;
        this._DEBOUNCE_DELAY = 500;
        this._currentFetchController = null;

        // Prop defaults
        this._isLoading = true;
        this._searchValue = "";
        this._themeSearchValue = "";
        this._stanceFilters = [];
        this._evidenceRichFilters = [];
        this._themeFilters = [];
        this._themesPanelVisible = false;
        this._demographicFilters = {};
        this._numberAnimationDuration = 500;
        this._searchDebounceTimer = null;
        this._currentPage = 1;
        this._hasMorePages = true;
        this._errorOccured = false;

        this.questionTitle = "";
        this.questionText = "";
        this.questionSlug = "";
        this.consultationTitle = "";
        this.consultationSlug = "";
        this.responses = [];
        this.responsesTotal = 0;
        this.themeMappings = [];
        this.stanceOptions = [];
        this.demographicOptions = {};
        this.free_text_question_part = false;
        this.has_multiple_choice_question_part = false;
        this.multiple_choice_summary = [];
        this.fetchData = window.fetch.bind(window);

        this.applyStaticStyles("iai-response-dashboard", IaiResponseDashboard.styles);
    }

    firstUpdated() {
        window.addEventListener("mousedown", this.handleThemesPanelClose);
    }

    fetchResponses = async () => {
        clearTimeout(this._searchDebounceTimer);

        this._searchDebounceTimer = setTimeout(async () => {
            if (!this._hasMorePages) {
                return;
            }

            if (this._currentFetchController) {
                console.log("aborting stale request");
                this._currentFetchController.abort();
            }

            const controller = new AbortController();
            const signal = controller.signal;
            this._currentFetchController = controller;

            this._errorOccured = false;
            this._isLoading = true;

            const url = `/consultations/${this.consultationSlug}/responses/${this.questionSlug}/json?` + this.buildQuery();

            let response;
            try {
                response = await this.fetchData(url, { signal });
            } catch (err) {
                if (err.name == "AbortError") {
                    console.log("stale request aborted");
                    return;
                } else {
                    console.error(err);
                    this._errorOccured = true;
                    return;
                }
            } finally {
                if (this._currentFetchController === controller) {
                    this._currentFetchController = null;
                }
                this._isLoading = false;
            }

            if (!response.ok) {
                this._errorOccured = true;
                throw new Error(`Response status: ${response.status}`);
            }

            const responsesData = await response.json();

            this.responses = this.responses.concat(
                responsesData.all_respondents.map(response => ({
                    ...response,
                    visible: true,
                }))
            );
            this.responsesTotal = responsesData.respondents_total;
            this._responsesFilteredTotal = responsesData.filtered_total;

            // Update theme mappings only on first page (when _currentPage === 1) to reflect current filters
            if (this._currentPage === 1 && responsesData.theme_mappings) {
                this.themeMappings = responsesData.theme_mappings;
            }

            // Update demographic options if available
            if (responsesData.demographic_options) {
                this.demographicOptions = responsesData.demographic_options;
            }

            this._hasMorePages = responsesData.has_more_pages;

            this._currentPage = this._currentPage + 1;
        }, this._DEBOUNCE_DELAY);
    }

    resetResponses = () => {
        this.responses = [];
        this._currentPage = 1;
        this._hasMorePages = true;
        this._isLoading = true;
    }

    updated(changedProps) {
        if (
            changedProps.has("_stanceFilters") ||
            changedProps.has("_evidenceRichFilters") ||
            changedProps.has("_searchValue")  ||
            changedProps.has("_themeFilters") ||
            changedProps.has("_demographicFilters")
        ) {
            this.resetResponses();
            this.fetchResponses();
            // this.applyFilters();
        }
    }

    disconnectedCallback() {
        window.removeEventListener("mousedown", this.handleThemesPanelClose);
    }

    handleSearchInput = (e) => {
        this._searchValue = e.target.value.trim();
    }
    handleStanceChange = (e) => {
        this._stanceFilters = this.addOrRemoveFilter(this._stanceFilters, e.target.value);
    }
    handleEvidenceRichChange = (e) => {
        this._evidenceRichFilters = this.addOrRemoveFilter(this._evidenceRichFilters, e.target.value);
    }
    handleThemeFilterChange = (e) => {
        this._themeFilters = this.addOrRemoveFilter(this._themeFilters, e.target.value);
    }
    handleDemographicChange = (field, value) => {
        if (!this._demographicFilters[field]) {
            this._demographicFilters[field] = [];
        }

        const currentValues = this._demographicFilters[field];
        const valueIndex = currentValues.indexOf(value);

        if (valueIndex > -1) {
            // Remove the value
            currentValues.splice(valueIndex, 1);
            if (currentValues.length === 0) {
                delete this._demographicFilters[field];
            }
        } else {
            // Add the value
            currentValues.push(value);
        }

        // Trigger reactive update
        this._demographicFilters = { ...this._demographicFilters };
    }

    getVisibleResponseTotal() {
        return this.responses.filter(response => response.visible).length;
    }

    handleThemesPanelClose = (e) => {
        const themesContainerEl = this.querySelector(".themes-container");

        if (!themesContainerEl) {
            return;
        }

        if (!themesContainerEl.contains(e.target)) {
            this._themesPanelVisible = false;
        }
    }

    addOrRemoveFilter = (filters, newFilter) => {
        if (filters.includes(newFilter)) {
            return filters.filter(filter => filter !== newFilter);
        } else {
            return [...filters, newFilter];
        }
    }

    applyFilters = () => {
        this.responses = this.responses.map(response => ({
            ...response,
            visible: this.getResponseVisibility(response),
        }));
    }

    getResponseVisibility = (response) => {
        let visible = true;

        // filter by search box text
        if (
            this._searchValue &&
            !response.free_text_answer_text.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()) &&
            !(typeof response.identifier === "string" && response.identifier.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())) &&
            !response.multiple_choice_answer.join(",").toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase())
        ) {
            visible = false;
        }

        // filter by themes selected
        if (this._themeFilters.length > 0) {
            if (!response.themes.find(theme => this._themeFilters.includes(theme.id))) {
                visible = false;
            }
        }

        // filter by stances selected
        if (this._stanceFilters.length > 0) {
            if (!this._stanceFilters.includes(response.sentiment_position)) {
                visible = false;
            }
        }

        // filter by evidence rich
        if (this._evidenceRichFilters.length > 0) {
            if (
                this._evidenceRichFilters.includes("evidence-rich") &&
                !response.evidenceRich
            ) {
                visible = false;
            }
        }

        return visible;
    }

    getAllThemes() {
        return this.responses.map(response => response.themes);
    }

    themeFilterInputVisible = (themeMapping) => {
        return (
            this._themeFilters.includes(themeMapping.value) ||
            themeMapping.label.toLocaleLowerCase().includes(this._themeSearchValue.toLocaleLowerCase())
        )
    }

    buildQuery = () => {
        // conditionally add filters as query params
        const params = new URLSearchParams({
            ...(this._searchValue && {
                searchValue: this._searchValue
            }),
            ...(this._stanceFilters.length > 0 && {
                sentimentFilters: this._stanceFilters.join(",")
            }),
            ...(this._themeFilters.length > 0 && {
                themeFilters: this._themeFilters.join(",")
            }),
            ...(this._evidenceRichFilters.length > 0 && {
                evidenceRichFilter: this._evidenceRichFilters.join(",")
            }),
            page: this._currentPage,
            page_size: this._PAGE_SIZE.toString(),
        });

        // Add demographic filters using square bracket notation
        Object.entries(this._demographicFilters).forEach(([field, values]) => {
            if (values.length > 0) {
                params.append(`demographicFilters[${field}]`, values.join(","));
            }
        });

        return params.toString();
    }

    getPercentage = (partialValue, totalValue) => {
        if (totalValue === 0) {
            return 0;
        }
        return Math.round(((partialValue / totalValue) * 100));
    }

    formatFieldName = (field) => {
        // Convert field name to Title Case and handle special cases
        return field
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatDemographicValue = (field, value) => {
        // Special formatting for boolean values
        if (value === "true" || value === "false") {
            return value === "true" ? "Yes" : "No";
        }
        // Capitalize first letter for other values
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    getResponsesMessage = () => {
        if (this._errorOccured) {
            return "Something went wrong";
        }
        if (this.responses.length === 0 && !this._isLoading) {
            return "No matching responses found";
        }
        return "";
    }

    render() {
        const visibleResponses = this.responses.filter(response => response.visible);

        return x`
            <div class="govuk-grid-row govuk-!-margin-top-5">
                <div class="govuk-grid-column-full">
                    <iai-page-title
                        .title=${x`
                            <div style="display: flex;">
                                <span style="margin-right: 1em;">${this.questionTitle}</span>
                                <span class="govuk-caption-m count-display">
                                    <strong>${this.responsesTotal}</strong> responses
                                </span>
                            </div>
                        `}
                        .subtitle=${this.consultationTitle}
                    ></iai-page-title>

                    <div class="question-text">
                        <iai-expanding-text
                            .text=${this.questionText}
                            .lines=${2}
                        ></iai-expanding-text>
                    </div>
                </div>
            </div>

            ${this.themeMappings.length > 0
                ? x`
                    <div class="govuk-grid-row govuk-!-margin-top-5">
                        <div class="govuk-grid-column-full">
                            <div class="table-container">

                                <div class="table-title themes-mentions">
                                    <div class="title-container">
                                        <h2 class="govuk-heading-m">
                                            Themes
                                        </h2>

                                        <button
                                            class="ternary-button"
                                            @click=${() => {
                                                const pills = Array.from(this.querySelectorAll("table iai-expanding-pill"));

                                                if (pills.filter(pill => !pill._expanded).length == 0) {
                                                    // If all pills are extended, collapse them all
                                                    pills.forEach(pill => pill._expanded = false);
                                                } else {
                                                    // else expand them all
                                                    pills.forEach(pill => pill._expanded = true);
                                                }
                                            }}
                                        >
                                            Hide/show all descriptions
                                        </button>
                                    </div>

                                    <iai-csv-download
                                        fileName="theme_mentions.csv"
                                        .data=${this.themeMappings
                                            .map(themeMapping => (
                                                {
                                                    "Theme name": themeMapping.label,
                                                    "Theme description": themeMapping.description,
                                                    "Total mentions": themeMapping.count,
                                                }
                                            ))
                                        }
                                    ></iai-csv-download>
                                </div>

                                <div class="theme-filters-applied">
                                    <ul>
                                        ${this._themeFilters.map(themeFilterId => x`
                                            <li>
                                                <iai-chip
                                                    .label=${this.themeMappings
                                                        .find(themeMapping => themeMapping.value == themeFilterId).label
                                                    }
                                                    .handleClick=${_ => this._themeFilters = this._themeFilters.filter(
                                                        currThemeFilterId => currThemeFilterId != themeFilterId
                                                    )}
                                                ></iai-chip>
                                            </li>
                                        `)}
                                    </ul>
                                </div>

                                <iai-data-table
                                    .initialSorts=${[
                                        {
                                            field: "Number of responses",
                                            ascending: false,
                                        }
                                    ]}
                                    .data=${this.themeMappings
                                        .map(themeMapping => (
                                            {
                                                // _sortValues are the values used for sorting comparison
                                                // instead of the actual value of a cell, which can be an obj etc.
                                                // particularly useful for html elements and dates.
                                                "_sortValues": {
                                                    "Theme name and description": themeMapping.label,
                                                    "Number of responses": parseInt(themeMapping.count),
                                                    "Percentage of responses": this.getPercentage(parseInt(themeMapping.count), this.responsesTotal),
                                                },
                                                "Theme name and description": x`
                                                    <iai-expanding-pill
                                                        .label=${themeMapping.label}
                                                        .body=${themeMapping.description}
                                                        .initialExpanded=${true}
                                                    ></iai-expanding-pill>
                                                `,
                                                "Percentage of responses": x`
                                                    <div class="percentage-cell">
                                                        <iai-animated-number
                                                            .number=${this.getPercentage(
                                                                parseInt(themeMapping.count),
                                                                this.responsesTotal
                                                            )}
                                                            .duration=${this._numberAnimationDuration}
                                                        ></iai-animated-number>
                                                        %
                                                    <div>
                                                `,
                                                "Number of responses": x`
                                                    <div class="total-count-cell">
                                                        <iai-progress-bar
                                                            .value=${this.getPercentage(parseInt(themeMapping.count), this.responsesTotal)}
                                                            .label=${themeMapping.count}
                                                        ></iai-progress-bar>
                                                    </div>
                                                `
                                            }
                                        ))
                                    }
                                ></iai-data-table>
                            </div>
                        </div>
                    </div>
                `
                : ""
            }

            ${this.multiple_choice_summary.length > 0
                ? x`
                    <div class="govuk-grid-row govuk-!-margin-top-5">
                        <div class="govuk-grid-column-full">
                            <div class="table-container">
                                <div class="table-title">
                                    <h2 class="govuk-heading-m">
                                        Multiple-Choice Responses
                                    </h2>
                                </div>

                                <iai-data-table
                                    .data=${this.multiple_choice_summary.map(item => ({
                                        "_sortValues": {
                                            "Count": parseInt(Object.values(item)[0]),
                                        },
                                        "Answer": Object.keys(item)[0],
                                        "Count": Object.values(item)[0],
                                    }))}
                                ></iai-data-table>
                            </div>
                        </div>
                    </div>
                `
                : ""
            }

            <div class="govuk-grid-row govuk-!-margin-top-5 responses-row">
                <div class="govuk-grid-column-one-quarter-from-desktop filters-column">
                    <iai-response-filters>
                        <form slot="filters" method="GET">
                            <div class="iai-filter__options">

                                ${this.free_text_question_part
                                    ? x`
                                        <iai-response-filter-group title="Themes">
                                            <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
                                                <div class="themes-container">
                                                    <div
                                                        class="input-container"
                                                        @focusin=${() => this._themesPanelVisible = true}
                                                    >
                                                        <iai-text-input
                                                            inputId="responses-search-input"
                                                            name="responses-search"
                                                            label="Search"
                                                            hideLabel=${true}
                                                            placeholder="Search..."
                                                            value=${this._themeSearchValue}
                                                            .handleInput=${e => this._themeSearchValue = e.target.value}
                                                        ></iai-text-input>

                                                        <div class=${"themes-panel" + (this._themesPanelVisible ? " visible" : "")}>
                                                            ${this.themeMappings.map(themeMapping => this.themeFilterInputVisible(themeMapping)
                                                                ? x`
                                                                    <iai-checkbox-input
                                                                        name="thememappings-filter"
                                                                        .inputId=${themeMapping.inputId}
                                                                        .label=${themeMapping.label}
                                                                        .value=${themeMapping.value}
                                                                        .checked=${this._themeFilters.includes(themeMapping.value)}
                                                                        .handleChange=${this.handleThemeFilterChange}
                                                                        @focusin=${() => this._themesPanelVisible = true}
                                                                    ></iai-checkbox-input>
                                                                `
                                                                : ""
                                                            )}
                                                        </div>
                                                    </div>

                                                    ${this._themeFilters.length > 0
                                                        ? x`
                                                            <div class="theme-filters-applied">
                                                                <ul>
                                                                    ${this._themeFilters.map(themeFilterId => x`
                                                                        <li>
                                                                            <iai-chip
                                                                                .label=${this.themeMappings
                                                                                    .find(themeMapping => themeMapping.value == themeFilterId).label
                                                                                }
                                                                                .handleClick=${_ => this._themeFilters = this._themeFilters.filter(
                                                                                    currThemeFilterId => currThemeFilterId != themeFilterId
                                                                                )}
                                                                            ></iai-chip>
                                                                        </li>
                                                                    `)}
                                                                </ul>
                                                            </div>
                                                        `
                                                        : ""
                                                    }
                                                </div>
                                            </div>
                                        </iai-response-filter-group>

                                        <hr />
                                    `
                                    : ""
                                }

                                ${this.demographicOptions && Object.keys(this.demographicOptions).length > 0 ?
                                    Object.entries(this.demographicOptions).map(([field, values]) => x`
                                        <iai-response-filter-group title="${this.formatFieldName(field)}">
                                            <div
                                                slot="content"
                                                class="govuk-checkboxes govuk-checkboxes--small"
                                                data-module="govuk-checkboxes"
                                                data-govuk-checkboxes-init=""
                                            >
                                                ${values.map((value, index) => x`
                                                    <iai-checkbox-input
                                                        name="demographic-filter-${field}"
                                                        inputId="demographic-${field}-${index}"
                                                        label="${this.formatDemographicValue(field, value)}"
                                                        value="${value}"
                                                        .handleChange=${() => this.handleDemographicChange(field, value)}
                                                    ></iai-checkbox-input>
                                                `)}
                                            </div>
                                        </iai-response-filter-group>
                                        <hr />
                                    `)
                                : ""}


                                <iai-response-filter-group title="Response sentiment">
                                    <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
                                        ${this.stanceOptions.map(option => x`
                                            <iai-checkbox-input
                                                name=${option.name}
                                                inputId=${option.inputId}
                                                label=${option.label}
                                                value=${option.value}
                                                .handleChange=${this.handleStanceChange}
                                            ></iai-checkbox-input>
                                        `)}
                                    </div>
                                </iai-response-filter-group>

                                <hr />

                                <iai-response-filter-group title="Evidence-rich responses">
                                    <div slot="content" class="govuk-checkboxes govuk-checkboxes--small">
                                        <iai-checkbox-input
                                            name="evidence-rich"
                                            inputId="show-evidence-rich"
                                            label="Only show evidence-rich"
                                            value="evidence-rich"
                                            .handleChange=${this.handleEvidenceRichChange}
                                        ></iai-checkbox-input>
                                    </div>
                                </iai-response-filter-group>
                            </div>
                        </form>
                    </iai-response-filters>
                </div>

                <div class="govuk-grid-column-three-quarters-from-desktop responses-column">
                    <div class="title-container">
                        <h2 class="govuk-heading-m">
                            Individual responses
                        </h2>

                        <span class="govuk-caption-m count-display">
                            ${this._isLoading
                                ? x`<strong>Loading</strong> responses`
                                : x`Viewing <strong>${this._responsesFilteredTotal}</strong> responses`
                            }
                        </span>

                        <iai-text-input
                            inputId="responses-search-input"
                            name="responses-search"
                            label="Search"
                            hideLabel=${true}
                            placeholder="Search..."
                            value=${this._searchValue}
                            .handleInput=${this.handleSearchInput}
                        ></iai-text-input>
                    </div>

                    <iai-virtual-list
                        class="flex-grow"
                        .data=${this._isLoading && this.responses.length === 0
                            ? [...Array(10).keys()].map(i => ({
                                id: "skeleton-response",
                                identifier: "skeleton-response",
                                free_text_answer_text: "Skeleton Body".repeat(50),
                                has_multiple_choice_question_part: false,
                                skeleton: true,
                              }))
                            : visibleResponses
                        }
                        .renderItem=${(response, index) => x`
                            <iai-response
                                class=${index === this.responses.length - 1 ? "last-item" : ""}
                                role="listitem"
                                .id=${response.inputId}
                                .identifier=${response.identifier}
                                .sentiment_position=${response.sentiment_position}
                                .free_text_answer_text=${response.free_text_answer_text}
                                .demographic_data=${response.demographic_data}
                                .themes=${response.themes}
                                .has_multiple_choice_question_part=${
                                response.hasOwnProperty("has_multiple_choice_question_part")
                                    ? response.has_multiple_choice_question_part
                                    : this.has_multiple_choice_question_part
                                }
                                .multiple_choice_answer=${response.multiple_choice_answer}
                                .searchValue=${this._searchValue}
                                .evidenceRich=${response.evidenceRich}
                                .skeleton=${response.skeleton}
                            ></iai-response>
                        `}
                        .handleScrollEnd=${() => {
                            if (this._isLoading) {
                                return;
                            }
                            this.fetchResponses();
                        }}
                        .isLoading=${this._isLoading}
                        .message=${this.getResponsesMessage()}
                    ></iai-virtual-list>

                    ${this._isLoading
                        ? x`<iai-loading-indicator></iai-loading-indicator>`
                        : ""
                    }
                </div>
            </div>
        `;
    }
}
customElements.define("iai-response-dashboard", IaiResponseDashboard);

class SearchBox extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: { type: String },
        label: { type: String },
        placeholder: { type: String },
        value: { type: String },
        hideLabel: { type: Boolean },
        handleInput: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-search-box .search-box-container {
                position: relative;
            }
            iai-silver-search-box .search-box-container input {
                padding-left: 2.5em;
                border-radius: 0.5em;
                background: var(--iai-silver-color-light);
                border: none;
            }
            iai-silver-search-box .search-box-container iai-icon {
                position: absolute;
                left: 0.5em;
                bottom: 0.5em;
            }
            iai-silver-search-box .clear-button {
                position: absolute;
                top: 50%;
                right: 2em;
                z-index: 1;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.placeholder = "";
        this.value = "";
        this.hideLabel = true;
        this.handleInput = () => {};

        this.applyStaticStyles("iai-silver-search-box", SearchBox.styles);
    }

    render() {
        return x`
            <div class="search-box-container">
                <iai-text-input
                    .inputId=${this.inputId}
                    .name=${this.name}
                    .label=${this.label}
                    .placeholder=${this.placeholder}
                    .value=${this.value}
                    .hideLabel=${this.hideLabel}
                    .handleInput=${this.handleInput}
                ></iai-text-input>

                <iai-icon
                    name="search"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>

                ${this.value
                    ? x`
                        <iai-icon-button
                            class="clear-button"
                            .title="Clear search"
                            @click=${() => {
                                this.value = "";
                                this.handleInput({target: {value: ""}});
                                this.querySelector("input").value = "";
                            }}
                        >
                            <iai-icon
                                slot="icon"
                                .name=${"close"}
                                .color=${"var(--iai-silver-color-text)"}
                            ></iai-icon>
                        </iai-icon-button>
                    `
                    : ""
                }
            </div>
        `;
    }
}
customElements.define("iai-silver-search-box", SearchBox);

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

class IaiSelectInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
        hideLabel: { type: Boolean },
        placeholder: { type: String },
        options: { type: Array },
        value: { type: String },
        handleInput: { type: Function },
        horizontal: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            .horizontal {
                display: flex;
                align-items: center;
                gap: 0.5em;
            }
            .horizontal label {
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.hideLabel = true;
        this.placeholder = "";
        this.options = [];
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-select-input", IaiSelectInput.styles);
    }

    render() {
        return x`
            <div class=${"govuk-form-group" + (this.horizontal ? " horizontal" : "")}>
                <label
                    class=${"govuk-label" + (this.hideLabel ? " visually-hidden" : "")}
                    for=${this.inputId}
                >
                    ${this.label}
                </label>
                <select
                    class="govuk-select"
                    .id=${this.inputId}
                    .name=${this.name}
                    .value=${this.value}
                    @change=${this.handleChange}
                >
                    ${[ // Add placeholder empty option to options
                        { value: "", text: this.placeholder },
                        ...this.options
                    ].map(option => {
                        if (!option.value && !this.placeholder) {
                            return "";
                        }
                        return x`
                            <option
                                .value=${option.value}
                                ?selected=${option.value === this.value}
                            >
                                ${option.text}
                            </option>
                        `})
                    }
                </select>
            </div>
        `
    }
}
customElements.define("iai-select-input", IaiSelectInput);

class SelectInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: { type: String },
        label: { type: String },
        hideLabel: { type: Boolean },
        placeholder: { type: String },
        options: { type: Array },
        value: { type: String },
        handleInput: { type: Function },
        horizontal: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-select-input iai-select-input select.govuk-select {
                border: none;
                background: var(--iai-silver-color-light);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.hideLabel = true;
        this.placeholder = "";
        this.options = [];
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-silver-select-input", SelectInput.styles);
    }

    render() {
        return x`
            <iai-select-input
                .inputId=${this.inputId}
                .name=${this.name}
                .label=${this.label}
                .hideLabel=${this.hideLabel}
                .placeholder=${this.placeholder}
                .options=${this.options}
                .value=${this.value}
                .handleChange=${this.handleChange}
                .horizontal=${this.horizontal}
            ></iai-select-input>
        `
    }
}
customElements.define("iai-silver-select-input", SelectInput);

class Card extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        color: { type: String },
        backgroundColor: { type: String },
        text: { type: String },
        number: { type: Number },
        icon: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-card {
                display: block;    
                width: max-content;
            }
            iai-silver-card p {
                margin: 0;
            }
            iai-silver-card .number {
                font-size: 1.3em;
            }
            iai-silver-card .text {
                font-size: 0.8em;
            }
            iai-silver-card div[slot="content"] {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 1em;
                padding: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.color = "white";
        this.backgroundColor = "black";
        this.text = "";
        this.number = 0;
        this.icon = "";

        this.applyStaticStyles("iai-silver-card", Card.styles);
    }

    render() {
        return x`
            <iai-silver-panel .borderColor=${this.color}>
                <div slot="content">
                    <iai-silver-icon-tile
                        .color=${this.color}
                        .backgroundColor=${this.backgroundColor}
                        .name=${this.name}
                    ></iai-silver-icon-tile>
                    <div>
                        <p class="text">${this.text}</p>
                        <p class="number">${this.number}</p>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-card", Card);

class Consultation extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        title: { type: String },
        description: { type: String },
        department: { type: String },
        numResponses: { type: Number },
        numQuestions: { type: Number },
        numThemes: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-consultation .topbar {
                display: flex;
                justify-content: space-between;
                margin-bottom: 1em;
            }
            iai-silver-consultation .topbar .tags {
                display: flex;    
                align-items: center;
                gap: 0.5em;
            }

            iai-silver-consultation .tag {
                padding: 0.3em 0.5em;
            }

            iai-silver-consultation .status {
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 0.8em;
                color: white;
                background: #85d07e;                
                border-radius: 0.5em;
            }
            iai-silver-consultation .department {
                font-size: 0.8em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.status = "";
        this.title = "";
        this.description = "";
        this.department = "";
        this.numResponses = 0;
        this.numQuestions = 0;
        this.numThemes = 0;

        this.applyStaticStyles("iai-silver-consultation", Consultation.styles);
    }

    getIconColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return "#85d07e";
            case this.CONSULTATION_STATUSES.analysing:
                return "#efdb5d";
            case this.CONSULTATION_STATUSES.completed:
                return "#0b8478";
            case this.CONSULTATION_STATUSES.closed:
                return "var(--iai-silver-color-text)";
            default:
                return "#85d07e";
        }
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return "#85d07e";
            case this.CONSULTATION_STATUSES.analysing:
                return "#efdb5d";
            case this.CONSULTATION_STATUSES.completed:
                return "#0b8478";
            case this.CONSULTATION_STATUSES.closed:
                return "#f8f9fa";
            default:
                return "#85d07e";
        }
    }

    render() {
        return x`
            <iai-silver-panel>
                <div slot="content">
                    <div class="topbar">
                        <div class="tags">
                            <iai-icon
                                name="schedule"
                                .color=${this.getIconColor(this.status)}
                            ></iai-icon>

                            <span class="tag status" style=${`background: ${this.getTagColor(this.status)}; color: ${this.status == this.CONSULTATION_STATUSES.closed ? "black" : "white"}`}>
                                ${this.status}
                            </span>

                            <span class="tag" style="border-radius: 0.5em; background: white; border: 1px solid var(--iai-silver-color-mid); padding-inline: 0.5em; font-size: 0.8em; display: flex; justify-content: center; align-items: center;">
                                Transport
                            </span>
                        </div>
                        <div>
                            <iai-silver-button
                                .text=${"View analysis"}
                                .handleClick=${() => console.log("button clicked")}
                            ></iai-silver-button>
                        </div>
                    </div>

                    <iai-silver-title
                        .text=${this.title}
                        .variant=${"secondary"}
                    ></iai-silver-title>

                    <p>
                        ${this.description}
                    </p>
                    
                    <div style="display: flex; gap: 1em;">
                        <div style="display: flex; align-items: center; gap: 0.25em; margin-bottom: 0.5em;">
                            <iai-icon
                                name="calendar_month"
                                color="var(--iai-silver-color-text)"
                            ></iai-icon>
                            <small>
                                4 May 2024 - 8 Aug 2024
                            </small>
                        </div>

                        <div style="display: flex; align-items: center; gap: 0.25em; margin-bottom: 0.5em;">
                            <iai-icon
                                name="group"
                                color="var(--iai-silver-color-text)"
                            ></iai-icon>
                            <small>
                                ${this.numResponses.toLocaleString()} responses
                            </small>
                        </div>

                        <div style="display: flex; align-items: center; gap: 0.25em; margin-bottom: 0.5em;">
                            <iai-icon
                                name="description"
                                color="var(--iai-silver-color-text)"
                            ></iai-icon>
                            <small>
                                ${this.numQuestions} questions
                            </small>
                        </div>

                        <div style="display: flex; align-items: center; gap: 0.25em; margin-bottom: 0.5em;">
                            <iai-icon
                                name="monitoring"
                                color="var(--iai-silver-color-text)"
                            ></iai-icon>
                            <small>
                                ${this.numThemes} themes
                            </small>
                        </div>
                    </div>

                    <small class="department">
                        ${this.department}
                    </small>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-consultation", Consultation);

class CrossSearchCard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        aside: { type: String },
        description: { type: String },
        tags: { type: Array }, //  Array<String>
        type: { type: String }, //  "question" | "response"
        highlightText: { type: String },
        footer: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-cross-search-card h3 {
                font-size: 0.9em;
                margin: 0;
            }
            iai-silver-cross-search-card .container {
                display: flex;
                gap: 0.5em;
            }
            iai-silver-cross-search-card .body-container {
                flex-grow: 1;
            }
            iai-silver-cross-search-card .title-container {
                display: flex;
                justify-content: space-between;
            }
            iai-silver-cross-search-card .tags {
                display: flex;
                gap: 0.5em;
                flex-wrap: wrap;
            }
            iai-silver-cross-search-card .tag {
                display: flex;
                justify-content: center;
                align-items: center;    
                padding: 0.3em 0.5em;
                background: #e6e6e7;
                font-size: 0.8em;
                border-radius: 0.5em;
            }
            iai-silver-cross-search-card .matched-text {
                background: yellow;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.aside = "";
        this.description = "";
        this.tags = [];
        this.type = "question";
        this.highlightText = "";
        this.footer = "";

        this.applyStaticStyles("iai-silver-cross-search-card", CrossSearchCard.styles);
    }

    applyTextHighlight = (text) => {
        if (!this.highlightText) {
            return text;
        }
        const regex = new RegExp(this.highlightText, "gi");
        return o$2(text.replace(regex, match => `<span class="matched-text">${match}</span>`));
    }

    render() {
        return x`
            <iai-silver-panel>
                <article slot="content">
                    <div class="container">
                        <div>
                            <iai-icon
                                .name=${this.type == "question" ? "help" : "chat_bubble"}
                                .color=${this.type == "question"
                                    ? "oklch(.6 .118 184.704)"
                                    : "oklch(.828 .189 84.429)"
                                }
                            ></iai-icon>
                        </div>

                        <div class="body-container">
                            <div class="title-container">
                                <h3>
                                    ${this.applyTextHighlight(this.title)}
                                </h3>

                                ${this.aside ? this.aside : ""}
                            </div>

                            <p>
                                ${this.applyTextHighlight(this.description)}
                            </p>

                            <footer class="tags">
                                ${this.footer}
                                ${this.tags.map(tag => x`
                                    <span class="tag">
                                        ${tag}
                                    </span>
                                `)}
                            </footer>
                        <div>
                    </div>
                </article>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-cross-search-card", CrossSearchCard);

class Tag extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        text: { type: String },
        subtext: { type: String },
        matchBackground: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-tag .tag {
                display: grid;
                width: max-content;
                max-width: 100%;
                gap: 0.5em; 
                padding: 0.3em 0.5em;
                font-size: 0.8em;
                line-height: 1.5em;
                color: white;
                border-radius: 0.5em;
            }
            iai-silver-tag iai-icon {
                margin-right: 0.3em;
            }
            iai-silver-tag iai-icon .material-symbols-outlined {
                font-size: 1.3em;
            }
            iai-silver-tag .text-container {
                display: flex;
                align-items: center;
                font-weight: bold;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.status = "";
        this.text = "";
        this.subtext = "";
        this.matchBackground = false;
        
        this.applyStaticStyles("iai-silver-tag", Tag.styles);
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                    ternary: "var(--iai-silver-color-teal-mid)",
                };
            case this.CONSULTATION_STATUSES.analysing:
                return {
                    primary: "var(--iai-silver-color-pink)",
                    secondary: "var(--iai-silver-color-pink-light)",
                    ternary: "var(--iai-silver-color-pink-mid)",
                };
            case this.CONSULTATION_STATUSES.completed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                    ternary: "var(--iai-silver-color-teal-mid)",
                };
            case this.CONSULTATION_STATUSES.closed:
                return {
                    primary: "var(--iai-silver-color-amber)",
                    secondary: "var(--iai-silver-color-amber-light)",
                    ternary: "var(--iai-silver-color-amber-mid)",
                };
            default:
                return {
                    primary: "var(--iai-silver-color-dark)",
                    secondary: "var(--iai-silver-color-light)",
                    ternary: "var(--iai-silver-color-mid-light)",
                };
        }
    }

    render() {
        return x`
            <style>
                #${this.contentId} {
                    color: ${this.getTagColor(this.status).primary};
                    background: ${this.matchBackground
                        ? this.getTagColor(this.status).ternary
                        : this.getTagColor(this.status).secondary
                    };
                    border: 1px solid ${this.getTagColor(this.status).ternary};
                }
            </style>
            
            <span id=${this.contentId} class="tag">
                <span class="text-container">
                    ${this.icon
                        ? x`
                            <iai-icon
                                .name=${this.icon}
                                .color=${this.getTagColor(this.status).primary}
                            ></iai-icon>
                        `
                        : ""
                    }
                    ${this.text}
                </span>

                ${this.subtext ? x`
                    <span>
                        ${this.subtext}
                    </span>    
                ` : ""}
            </span>
        `
    }
}
customElements.define("iai-silver-tag", Tag);

class QuestionOverviewPage extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        questions: { type: Array },
        consultationName: { type: String },
        _searchValue: { type: String },
        _favouritedQuestions: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-overview-page {
                color: var(--iai-silver-color-text);
            }
            iai-question-overview-page section {
                margin-bottom: 2em;
            }
            iai-question-overview-page ul {
                padding-left: 0;
            }
            iai-question-overview-page li {
                list-style: none;
                margin-top: 1em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-question-overview-page li:hover {
                background: var(--iai-silver-color-light);
            }
            iai-question-overview-page iai-silver-cross-search-card .icon-container {
                margin-bottom: 0;
            }
            iai-question-overview-page .response-total {
                display: flex;
                align-items: center;
            }
            iai-question-overview-page .favourite-button {
                margin-top: -0.4em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.consultationName = "";
        this.questions = [];

        this._searchValue = "";
        this._favouritedQuestions = [];

        this.applyStaticStyles("iai-question-overview-page", QuestionOverviewPage.styles);
    }

    firstUpdated() {
        this._favouritedQuestions = this.getStoredValues(this._STORAGE_KEYS.FAVOURITE_QUESTIONS);
    }

    renderSearchCard(question, index) {
        return x`
            <iai-silver-cross-search-card
                @click=${() => window.location.href = question.url}
                .type=${"question"}
                .title=${question.title}
                .aside=${x`
                    <iai-icon-button
                        class="favourite-button"
                        title="Favourite this question"
                        @click=${(e) => {
                            e.stopPropagation();
                            this.toggleStorage(question.id, this._STORAGE_KEYS.FAVOURITE_QUESTIONS);
                            this._favouritedQuestions = this.getStoredValues(this._STORAGE_KEYS.FAVOURITE_QUESTIONS);
                        }}
                    >
                        <iai-icon
                            slot="icon"
                            name="star"
                            .color=${"var(--iai-silver-color-text)"}
                            .fill=${this._favouritedQuestions.includes(question.id) ? 1 : 0}
                        ></iai-icon>
                    </iai-icon-button>
                `}
                .footer=${x`
                    <small class="response-total">
                        ${question.numResponses.toLocaleString()} responses
                    </small>
                    <iai-silver-tag
                        .status=${question.status}
                        .text=${question.status}
                        .icon=${"chat_bubble"}
                    ></iai-silver-tag>
                `}
                .highlightText=${this._searchValue}
            ></iai-silver-cross-search-card>
        `
    }

    render() {
        return x`
            <section>
                <iai-silver-title
                    .level=${2}
                    .text=${"Favourited Questions"}
                    .icon=${"star"}
                ></iai-silver-title>

                <iai-silver-panel>
                    <div slot="content">
                        <ul>
                            ${this.questions
                                .filter(question => this._favouritedQuestions.includes(question.id))
                                .map((question, index) => x`
                                <li>
                                    ${this.renderSearchCard(question, index)}
                                </li>
                            `)}
                        </ul>
                    </div>
                </iai-silver-panel>
            </section>

            <section>
                <iai-silver-title
                    .level=${2}
                    .text=${"All consultation questions"}
                    .subtext=${"Browse or search through all questions in this consultation."}
                    .aside=${x`<small>${this.questions.length} questions</small>`}
                    .icon=${"help"}
                ></iai-silver-title>

                <iai-silver-panel>
                    <div slot="content">

                        <iai-silver-search-box
                            .inputId=${"search-value"}
                            .name=${"search-value"}
                            .label=${"Search"}
                            .placeholder=${"Search..."}
                            .value=${this._searchValue}
                            .hideLabel=${true}
                            .handleInput=${(e) => this._searchValue = e.target.value.trim()}
                        ></iai-silver-search-box>

                        <ul>
                            ${this.questions
                                .filter(question => !this._searchValue
                                    || question.title.toLocaleLowerCase().includes(this._searchValue.toLocaleLowerCase()))
                                .map((question, index) => x`
                                <li>
                                    ${this.renderSearchCard(question, index)}
                                </li>
                            `)}
                        </ul>

                    </div>
                </iai-silver-panel>
            </section>
        `
    }
}
customElements.define("iai-question-overview-page", QuestionOverviewPage);

class ToggleInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        label: { type: String },
        hideLabel: { type: Boolean },
        checked: {type: Boolean },
        value: { type: String },
        handleChange: { type: Function },
        name: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-toggle-input {
                --handle-size: 1.2em;
                display: flex;
                gap: 1em;
                align-items: center;
            }
            iai-toggle-input input {
                opacity: 0;
                position: absolute;
                z-index: -1;
            }
            iai-toggle-input label {
                cursor: pointer;
            }
            iai-toggle-input label.slider {
                position: relative;
                display: inline-block;
                width: 3em;
                height: 1.5em;
                background: var(--iai-silver-color-mid);
                border-radius: 5em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-toggle-input label.slider:before {
                content: "";
                position: absolute;
                height: var(--handle-size);
                width: var(--handle-size);
                border-radius: 50%;
                background: white;
                left: calc(var(--handle-size) / 5);
                top: calc(var(--handle-size) / 9);
                transition: left 0.3s ease-in-out;
                cursor: pointer;
            }
            iai-toggle-input label.slider:has(input:focus),
            iai-toggle-input label.slider:has(input:focus-visible) {
                outline: 0.3em solid var(--iai-colour-focus);
            }
            iai-toggle-input label.slider:has(input[data-checked="true"]) {
                background: var(--iai-silver-color-dark);
            }
            iai-toggle-input label.slider:has(input[data-checked="true"])::before {
                left: calc(45% + var(--handle-size) / 5);
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.label = "";
        this.checked = false;
        this.value = "";
        this.handleChange = () => {};
        this.name = "";

        this.applyStaticStyles("iai-toggle-input", ToggleInput.styles);
    }

    updated(changedProps) {
        if (changedProps.has("checked")) {
            this.querySelector("input").checked = this.checked;
        }
    }

    render() {
        return x`
            <label for=${this.inputId} class=${this.hideLabel ? "visually-hidden" : ""}>
                ${this.label}
            </label>
            <label class="slider" for=${this.inputId}>
                <input
                    type="checkbox"
                    id=${this.inputId}
                    name=${this.name}
                    value=${this.value}
                    @click=${this.handleChange}
                    data-checked=${this.checked ? "true" : "false"}
                >
            </label>
        `
    }
}
customElements.define("iai-toggle-input", ToggleInput);

class ThemesTable extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        themes: { type: Array },
        themeFilters: { type: Array },
        setThemeFilters: { type: Function },
        totalResponses: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-themes-table iai-data-table {
                display: block;
                overflow-x: auto;
            }
            iai-themes-table .theme-title {
                font-weight: bold;
                font-size: 0.9em;
                color: var(--iai-silver-color-text);
            }
            iai-themes-table .theme-description {
                display: block;
                font-size: 0.9em;
                min-width: 20em;
            }
            iai-themes-table .percentage-cell {
                gap: 0.5em;
                display: flex;
                align-items: center;
            }
            iai-themes-table .title-container {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-themes-table input[type="checkbox"] {
                filter: grayscale(0.5) hue-rotate(75deg);
            }

            iai-themes-table .percentage-cell iai-progress-bar .bar {
                background: var(--iai-silver-color-accent);
            }
            iai-themes-table .percentage-cell iai-progress-bar .container {
                background: var(--iai-silver-color-mid-light);
            }

            iai-themes-table iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-themes-table input {
                cursor: pointer;
            }
            iai-themes-table tr {
                transition: background 0.3s ease-in-out;
            }
            iai-themes-table tr:has(input:checked) {
                background: var(--iai-silver-color-teal-light);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._NUMBER_ANIMATION_DURATION = 1000;

        this.themes = [];
        this.themeFilters = [];
        this.setThemeFilters = () => {};
        this.totalResponses = 0;

        this.applyStaticStyles("iai-themes-table", ThemesTable.styles);
    }

    render() {
        return x`
            <iai-data-table
                .sortable=${false}
                .data=${this.themes
                    .map(theme => (
                        {
                            // _sortValues are the values used for sorting comparison
                            // instead of the actual value of a cell, which can be an obj etc.
                            // particularly useful for html elements and dates.
                            "_sortValues": {
                                "Mentions": parseInt(theme.mentions),
                                "Percentage": parseInt(theme.percentage),
                                "Theme": theme.title,
                            },
                            "_handleClick": () => this.setThemeFilters(theme.id),
                            "Theme": x`
                                <div class="title-container">
                                    <div>
                                        <input
                                            type="checkbox"
                                            class="theme-checkbox"
                                            id=${"theme-filters" + theme.title.toLowerCase().replace(" ", "-")}
                                            name="theme-filters"
                                            .value=${theme.id}
                                            .checked=${this.themeFilters.includes(theme.id)}
                                            @click=${(e) => {
                                                e.stopPropagation();
                                                this.setThemeFilters(e.target.value);
                                            }}
                                        />
                                    </div>
                                    <div>
                                        <span class="theme-title">
                                            ${theme.title}
                                        </span>
                                        <span class="theme-description">
                                            ${theme.description}
                                        </span>
                                    </div>
                                </div>
                            `,
                            "Mentions": x`
                                <iai-animated-number
                                    .number=${theme.mentions}
                                    .duration=${this._NUMBER_ANIMATION_DURATION}
                                ></iai-animated-number>
                            `,
                            "Percentage": x`
                                <div class="percentage-cell">
                                    <div>
                                        <iai-animated-number
                                            .number=${this.getPercentage(theme.mentions, this.totalResponses)}
                                            .duration=${this._NUMBER_ANIMATION_DURATION}
                                        ></iai-animated-number>
                                        %
                                    </div>

                                    <iai-progress-bar
                                        .value=${this.getPercentage(theme.mentions, this.totalResponses)}
                                        .label=${""}
                                    ></iai-progress-bar>
                                </div>
                            `,
                            "Actions": x`
                                <iai-silver-button
                                    .text=${x`
                                        <iai-icon
                                            .name=${"search"}
                                        ></iai-icon>
                                        <span>View responses</span>
                                    `}
                                    .handleClick=${(e) => {
                                        e.stopPropagation();
                                        theme.handleClick();
                                    }}
                                ></iai-silver-button>
                            `
                        }
                    ))
                }
            ></iai-data-table>
        `;
    }
}
customElements.define("iai-themes-table", ThemesTable);

class ThemeFiltersWarning extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        themes: { type: Array },
        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-theme-filters-warning .theme-tag .material-symbols-outlined {
                font-size: 1.3em;
            }
            iai-theme-filters-warning iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-filters-warning iai-silver-tag {
                width: 100%;
                display: block;
                margin-bottom: 1em;
            }
            iai-theme-filters-warning .tag-container iai-silver-tag {
                width: auto;
                margin: 0;
            }
            iai-theme-filters-warning iai-silver-tag .tag-container {
                display: flex;
                gap: 0.5em;
                align-items: center;
                flex-wrap: wrap;
            }
            iai-theme-filters-warning iai-silver-tag .theme-tag {
                display: flex;
                gap: 0.5em;
                font-size: 1.2em;
                align-items: center;
            }
            iai-theme-filters-warning iai-silver-tag .theme-tag iai-icon-button {
                margin-top: 0.1em;
            }
            iai-theme-filters-warning iai-silver-tag .tag {
                width: 100%;
            }
            iai-theme-filters-warning iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this.themes = [];
        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.applyStaticStyles("iai-theme-filters-warning", ThemeFiltersWarning.styles);
    }
    
    render() {
        return x`
            <iai-silver-tag
                .status=${"Analysing"}
                .icon=${"report"}
                .text=${`Selected themes (${this.themeFilters.length})`}
                .subtext=${x`
                    <div class="tag-container">
                        ${this.themeFilters.map(themeFilter => x`
                        <iai-silver-tag
                            .text=${x`
                                <div class="theme-tag">
                                    ${this.themes.find(theme => theme.id == themeFilter).title}

                                    <iai-icon-button .handleClick=${() => this.updateThemeFilters(themeFilter)}>
                                        <iai-icon
                                            slot="icon"
                                            .name=${"close"}
                                        ></iai-icon>
                                    </iai-icon-button>
                                    
                                </div>`}
                        ></iai-silver-tag>
                        `)}

                        <iai-silver-button
                            .text=${"Clear all"}
                            .handleClick=${() => this.updateThemeFilters()}
                        ></iai-silver-button>
                    </div>
                `}
            >
            </iai-silver-tag>
        `;
    }
}
customElements.define("iai-theme-filters-warning", ThemeFiltersWarning);

class MultiDropdown extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        text: { type: String },
        options: { type: Array }, //  { id, checked, title, handleClick }

        _panelVisible: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-multi-dropdown label,
            iai-multi-dropdown select,
            iai-multi-dropdown input {
                //font-size: 0.9em !important;
            }
            iai-multi-dropdown label {
                cursor: pointer;
                word-break: break-word;
                line-height: 1.5em;
            }
            iai-multi-dropdown .filters {
                display: flex;
                gap: 1em;
                width: 100%;
                flex-direction: column;
            }
            iai-multi-dropdown input[type="checkbox"] {
                width: auto;
                filter: grayscale(0.5) hue-rotate(75deg);
                cursor: pointer;
            }

            iai-multi-dropdown ul {
                list-style: none;
                padding-left: 0;
                margin: 0;
            }
            iai-multi-dropdown ul li {
                display: flex;
                gap: 0.5em;
                justify-content: flex-start;
                margin-bottom: 0.5em;
            }
            
            iai-multi-dropdown .popup-button .popup-panel {
                position: absolute;
                top: 2em;
                width: max-content;
                max-width: 80vw;
                max-height: 20em;
                overflow: auto;
                right: 0;
                background: white;
                padding: 1em;
                margin: 0;
                z-index: 2;
                border: 1px solid var(--iai-silver-color-mid);
                border-radius: 0.5em;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
                box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
            }
            iai-multi-dropdown .popup-button {
                position: relative;
            }
            iai-multi-dropdown .popup-button .popup-panel.left-placement {
                right: unset;
                left: 0;
            }
            iai-multi-dropdown .popup-panel .content {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-multi-dropdown .popup-button .icon-container {
                margin-bottom: 0.5em;
            }
            iai-multi-dropdown .popup-button iai-silver-title {
                color: var(--iai-silver-color-dark);
                cursor: pointer;
            }
            iai-multi-dropdown .popup-button .popup-button__body {
                position: relative;
            }
            iai-multi-dropdown .popup-button .popup-button__body iai-silver-button button {
                width: 100%;    
                line-height: 2em;
                background: var(--iai-silver-color-light);
                border: none;
                border-radius: 0.3em;
            }
            iai-multi-dropdown .popup-button .popup-button__text {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.text = "";
        this.options = [];

        this._panelVisible = false;
        this._leftPlacement = false;
        
        this.applyStaticStyles("iai-multi-dropdown", MultiDropdown.styles);
    }

    handleOutsideClick = (e) => {
        if (!this.contains(e.target)) {
            this._panelVisible = false;
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.setupPanelListeners(window.addEventListener);    }

    disconnectedCallback() {
        this.setupPanelListeners(window.removeEventListener);
        super.disconnectedCallback();
    }

    setupPanelListeners = (func) => {
        ["click", "touchstart"].forEach(eventName => {
            func(eventName, this.handleOutsideClick);
        });
    }

    isLeftPlaced = () => {
        const buttonEl = this.querySelector("iai-silver-button");
        if (!buttonEl) {
            return;
        }

        const rect = buttonEl.getBoundingClientRect();

        const elementCenter = rect.left + rect.width / 2;
        const screenCenter = window.innerWidth / 2;

        return elementCenter < screenCenter;
    }

    willUpdate(changedProps) {
        if (changedProps.has("_panelVisible")) {
            this._leftPlacement = this.isLeftPlaced();
        }
    }

    render() {
        return x`
            <div class="popup-button">
                <iai-silver-title
                    .level=${3}
                    .text=${this.title}
                    @click=${() => this._panelVisible = !this._panelVisible}
                ></iai-silver-title>

                <div class="popup-button__body">
                    <iai-silver-button
                        .text=${x`
                            <div class="popup-button__text">
                                <span>
                                    ${this.text}
                                </span>
                                <iai-icon
                                    .name=${"keyboard_arrow_down"}
                                ></iai-icon>
                            </div>
                        `}
                        .handleClick=${() => this._panelVisible = !this._panelVisible}
                    ></iai-silver-button>

                    ${this.options.length > 0 ? x`
                        <div
                            class=${"popup-panel" + (this._leftPlacement ? " left-placement" : "")}
                            style=${`
                                opacity: ${this._panelVisible ? 1 : 0};
                                pointer-events: ${this._panelVisible ? "auto" : "none"};
                            `}
                        >
                            <div class="content">
                                <ul>
                                    ${this.options.map(option => {
                                        const optionId = `${this.contentId}-${option.id.replace(" ", "-")}`;

                                        return x`
                                            <li>
                                                <input
                                                    type="checkbox"
                                                    class="theme-checkbox"
                                                    id=${optionId}
                                                    name=${`multi-dropdown-${this.contentId}`}
                                                    .value=${option.id}
                                                    .checked=${option.checked}
                                                    @click=${option.handleClick}
                                                />
                                                <label for=${optionId}>
                                                    ${option.title}
                                                </label>
                                            </li>
                                        `}
                                    )}
                                </ul>
                            </div>
                        </div>
                    ` : ""}
                </div>
                
            </div>
        `
    }
}
customElements.define("iai-multi-dropdown", MultiDropdown);

class ThemeAnalysis extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        consultationSlug: { type: String },
        themes: { type: Array },
        demoData: { type: Object },
        demoOptions: { type: Object },
        totalResponses: { type: Number },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },

        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },

        sortType: { type: String },
        setSortType: { type: Function },

        sortDirection: { type: String },
        setSortDirection: { type: Function },

        demoFilters: { type: Object },
        setDemoFilters: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-theme-analysis div[slot="content"] {
                padding-block: 0.5em;
            }
            iai-theme-analysis iai-silver-icon-tile {
                font-size: 0.8em;
            }
            iai-theme-analysis .theme-title {
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .percentage-cell {
                gap: 0.5em;
                display: flex;
                align-items: center;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar {
                flex-grow: 1;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .container {
                border-radius: 0.5em;
                background: var(--iai-silver-color-mid);
                border: none;
                opacity: 0.7;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .bar {
                height: 0.5em;
                border-top-left-radius: 0.5em;
                border-bottom-left-radius: 0.5em;
                background: var(--iai-silver-color-dark);
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .bar.full {
                border-radius: 0.5em;
            }
            iai-theme-analysis iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .filters-row {
                display: grid;
                gap: 1em;
            }
            iai-theme-analysis .total-themes {
                display: flex;
                flex-direction: column;    
                max-height: max-content;
                padding: 1em;
                font-size: 0.8em;
                white-space: nowrap;
                background: #fcf1f6;
                border-radius: 0.5em;
            }
            iai-theme-analysis .total-themes span {
                font-size: 1.5em;
                font-weight: bold;
            }
            iai-theme-analysis .filters-row {
                margin-bottom: 1em;
                background: var(--iai-silver-color-light);
                padding: 1em;
                border-radius: 0.5em;
            }
            iai-theme-analysis .filters {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                align-items: center;
            }
            iai-theme-analysis .filters iai-silver-select-input{
                white-space: nowrap;
            }
            iai-theme-analysis .top-panel {
                margin-bottom: 2em;
            }
            iai-theme-analysis .filters select.govuk-select {
                font-size: 0.9em;
                background: var(--iai-silver-color-light-darker);
            }
            iai-theme-analysis iai-multi-dropdown button {
                background: var(--iai-silver-color-light-darker) !important;
            }
            iai-theme-analysis .export-button button {
                padding-block: 0.2em;
            }
            iai-theme-analysis .filters .demographics-title .icon-container {
                margin: 0;
                color: var(--iai-silver-color-dark);
            }
            iai-theme-analysis .filters .govuk-form-group:has(select){
                margin: 0;
            }
            iai-theme-analysis .info-container {
                display: flex;
                justify-content: space-between;
            }
            @media (min-width: 40.0625em) {
                .govuk-form-group {
                    margin-bottom: 0;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._NUMBER_ANIMATION_DURATION = 1000;

        this.themes = [];
        this.demoData = {};
        this.demoOptions = {};
        this.totalResponses = 0;

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};

        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.demoFilters = {};
        this.setDemoFilters = () => {};
        
        this.sortType = "";
        this.setSortType = () => {};

        this.sortDirection = "";
        this.setSortDirection = () => {};

        this.applyStaticStyles("iai-theme-analysis", ThemeAnalysis.styles);
    }

    render() {
        return x`
            <iai-silver-panel>
                <div slot="content">
                    <div class="top-panel">
                        <iai-silver-title
                            .text=${"Theme analysis"}
                            .variant=${"secondary"}
                            .icon=${"lan"}
                            .aside=${x`
                                <iai-csv-download
                                    .fileName=${`theme_mentions_for_${this.consultationSlug}.csv`}
                                    .variant=${"silver"}
                                    .data=${
                                        this.themes.map(theme => ({
                                            "Theme Name": theme.title,
                                            "Theme Description": theme.description,
                                            "Mentions": theme.mentions,
                                            "Percentage": this.getPercentage(theme.mentions, this.totalResponses),
                                        }))
                                    }
                                >
                                </iai-csv-download>
                            `}
                        ></iai-silver-title>

                        <div class="filters-row">
                            <div class="filters">
                                <iai-silver-select-input
                                    .inputId=${"sort-value"}
                                    .name=${"sort-value"}
                                    .label=${"Sort by:"}
                                    .hideLabel=${false}
                                    .value=${this.sortType}
                                    .options=${[
                                        { value: "frequency", text: "Frequency" },
                                        { value: "alphabetical", text: "A-Z" },
                                    ]}
                                    .handleChange=${(e) => this.setSortType(e.target.value)}
                                    .horizontal=${true}
                                ></iai-silver-select-input>

                                <iai-icon-button .handleClick=${
                                    () => this.setSortDirection(this.sortDirection === "ascending"
                                        ? "descending"
                                        : "ascending"
                                )}>
                                    <iai-icon
                                        slot="icon"
                                        .name=${this.sortDirection === "ascending"
                                            ? "arrow_downward"
                                            : "arrow_upward"
                                        }
                                    ></iai-icon>
                                </iai-icon-button>
                            </div>

                            <div class="filters">
                                ${Object.keys(this.demoOptions).map(category => {
                                    return x`
                                        <iai-multi-dropdown
                                            .title=${category}
                                            .text=${`${this.demoFilters[category]?.length || 0} filters selected`}
                                            .options=${this.demoOptions[category].map(option => ({
                                                id: option,
                                                checked: Boolean(this.demoFilters[category]?.includes(option)),
                                                title: option,
                                                handleClick: (e) => {
                                                    this.setDemoFilters(category, option);
                                                },
                                            }))}
                                        ></iai-multi-dropdown>
                                    `
                                })}
                            </div>

                            ${this.themeFiltersApplied() || this.demoFiltersApplied() ? x`
                                <iai-silver-button
                                    .text=${"Clear filters"}
                                    .handleClick=${() => {
                                        this.updateThemeFilters();
                                        this.setDemoFilters();
                                    }}
                                ></iai-silver-button>
                            ` : ""}
                        </div>

                        ${this.themeFilters.length > 0 ? x`
                            <iai-theme-filters-warning
                                .themes=${this.themes}
                                .themeFilters=${this.themeFilters}
                                .updateThemeFilters=${this.updateThemeFilters}
                            ></iai-theme-filters-warning>
                        ` : ""}
                        
                        <div class="info-container">
                            <small>
                                Total Themes
                                <span>${this.themes.length}<span>
                            </small>

                            <small>
                                <!-- optional microcopy -->
                            </small>
                        </div>
                    </div>

                    <iai-themes-table
                        .themes=${this.themes}
                        .themeFilters=${this.themeFilters}
                        .setThemeFilters=${this.updateThemeFilters}
                        .totalResponses=${this.totalResponses}
                    ></iai-themes-table>
                </div>
            </iai-silver-panel>
        `;
    }
}
customElements.define("iai-theme-analysis", ThemeAnalysis);

class QuestionTitle extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        title: { type: String },
        description: { type: String },
        department: { type: String },
        numResponses: { type: Number },
        numQuestions: { type: Number },
        numThemes: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-question-title {
                color: var(--iai-silver-color-text);
            }
            iai-silver-question-title .topbar {
                display: flex;
                justify-content: space-between;
                margin-bottom: 1em;
            }
            iai-silver-question-title .topbar .tags {
                display: flex;    
                align-items: center;
                gap: 0.5em;
            }

            iai-silver-question-title .tag {
                padding: 0.3em 0.5em;
            }

            iai-silver-question-title .status {
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 0.8em;
                color: white;
                background: #85d07e;                
                border-radius: 0.5em;
            }
            iai-silver-question-title .responses {
                font-weight: bold;
            }
            iai-silver-question-title .department {
                font-size: 0.8em;
            }

            iai-silver-question-title iai-silver-button button {
                padding: 0.3em;
                border: none;
                font-size: 1.5em;
            }
            iai-silver-question-title .details {
                display: flex;
                align-items: center;
                gap: 1em;
                flex-wrap: wrap;
                margin-top: 1em;
            }
            iai-silver-question-title .title-container {
                display: flex;
                justify-content:
                space-between; gap: 1em;
                line-height: 1.5em;
            }
            iai-silver-question-title [slot="content"] {
                padding-block: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.status = "";
        this.title = "";
        this.department = "";
        this.numResponses = 0;

        this.applyStaticStyles("iai-silver-question-title", QuestionTitle.styles);
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.analysing:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.completed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.closed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
        }
    }

    render() {
        return x`
            <style>
                #${this.contentId} .tag.status {
                    color: ${this.getTagColor(this.status).primary};
                    background: ${this.getTagColor(this.status).secondary};
                    border: 1px solid ${this.getTagColor(this.status).primary};
                }
            </style>
            <iai-silver-panel id=${this.contentId}>
                <div slot="content">
                    <div class="title-container">
                        <iai-silver-title
                            .text=${this.title}
                            .level=${2}
                        ></iai-silver-title>

                        <iai-silver-button
                            .text=${x`
                                <iai-icon
                                    .name=${"star"}
                                    .color=${"var(--iai-silver-color-text)"}
                                ></iai-icon>
                            `}
                            .handleClick=${() => console.log("button clicked")}
                        ></iai-silver-button>
                    </div>

                    <div class="details">
                        <small class="responses">
                            ${this.numResponses.toLocaleString()} responses
                        </small>

                        <span class="tag status">
                            ${this.status}
                        </span>

                        <small class="department">
                            ${this.department}
                        </small>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-question-title", QuestionTitle);

class TabView extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        tabs: { type: Array },
        activeTab: { type: String },
        handleTabChange: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-tab-view nav {
                display: flex;
                max-width: max-content;
                margin: auto;
                margin-bottom: 1em;
                border-radius: 10em;
                font-size: 0.9em;
                background: var(--iai-silver-color-mid-light);
            }
            iai-tab-view .tab-button {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 0.5em;
                margin: 0.3em;
                padding: 0.5em;
                border-radius: 10em;
                list-style: none;
                text-align: center;
                font-size: 0.9em;
                color: var(--iai-silver-color-dark);
                transition: 0.3s ease-in-out;
                cursor: pointer;
            }
            iai-tab-view .tab-button:hover {
                background: var(--iai-silver-color-light);
            }
            iai-tab-view .tab-button.active {
                color: var(--iai-silver-color-dark);
                background: white;
            }
            iai-tab-view .tab-button .material-symbols-outlined {
                font-size: 1.3em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        console.log(this.tabs);
        this.tabs = [];
        this.activeTab = 0;
        this.handleTabChange = () => {};

        this.applyStaticStyles("iai-tab-view", TabView.styles);
    }

    render() {
        return x`
            <nav>
                ${this.tabs.map((tab, index) => x`
                    <li
                        role="button"
                        tabindex="0"
                        class=${"tab-button" + (this.activeTab === index ? " active" : "")}
                        @click=${() => this.handleTabChange(index)}
                    >
                        ${tab.title}
                    </li>
                `)}
            </nav>
            <div>
                ${this.tabs.map((tab, index) => x`
                    <section class=${this.activeTab === index ? "" : "visually-hidden"}>
                        ${tab.content}
                    </section>
                `)}
            </div>
        `;
    }
}
customElements.define("iai-tab-view", TabView);

class CrossSearch extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        searchValue: { type: String },
        searchMode: { type: String },
        searchType: { type: String },
        searchHighlight: { type: Boolean },
        _settingsVisible: { type: Boolean },

        results: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-cross-search {
                color: var(--iai-silver-color-text);
            }
            iai-silver-cross-search section {
                margin-block: 2em;
            }
            iai-silver-cross-search .govuk-form-group {
                margin: 0;
            }

            iai-silver-cross-search .cards {
                display: flex;
                gap: 1em;
                justify-content: space-between;
                margin-block: 2em;
            }
            iai-silver-cross-search .cards iai-silver-card {
                width: 23%;
            }


            iai-silver-cross-search div[slot="content"] {
                padding: 1em;
            }
            iai-silver-cross-search .inputs {
                display: flex;
                justify-content: space-between;
                gap: 1em;
                margin-block: 0.5em;
                flex-wrap: wrap;
            }
            iai-silver-cross-search div[slot="content"] .info {
                display: flex;
                gap: 0.5em;
                margin-top: 0.5em;
            }
            iai-silver-cross-search small {
                display: flex;
                align-items: center;
                font-size: 0.8em;
            }
            iai-silver-cross-search .inputs .group {
                display: flex;
                gap: 1em;
                flex-wrap: wrap;
                position: relative;
            }
            iai-silver-cross-search .inputs .popup {
                position: absolute;
                top: 2em;
                width: max-content;
                right: 0;
                background: white;
                padding: 1em;
                margin: 0;
                z-index: 2;
                border: 1px solid var(--iai-silver-color-mid);
                border-radius: 0.5em;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
                box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
            }
            iai-silver-cross-search .inputs iai-icon-button button:hover {
                background-color: var(--iai-silver-color-light);
            }
           
            iai-silver-cross-search iai-silver-search-box {
                flex-grow: 1;
            }
            
            iai-silver-cross-search ul.results-list {
                display: flex;
                flex-direction: column;
                gap: 1.5em;
                list-style: none;
                padding-left: 0;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.searchValue = "";
        this.searchMode = "keyword";
        this.searchType = "all";
        this.searchHighlight = true;
        this._settingsVisible = false;

        this.results = [
            {
                title: "DGSF air quality consultation",
                description: "Public consultation on air quality improvement measures and policy recommendations for local communities.",
                type: "question",
            },
            {
            
                title: "Future of Transport Strategy",
                description: "Consultation on sustainable transport infrastructure and policies for the next decade.",
                type: "response",
            },
            {
                title: "Digital Services Accessibility Standards",
                description: "Review of accessibility requirements for government digital services and public websites.",
                type: "question",
            },
            {
                title: "Social Housing Policy Review",
                description: "Comprehensive review of social housing policies and affordable housing provision.",
                type: "response",
            },
        ];

        this.applyStaticStyles("iai-silver-cross-search", CrossSearch.styles);
    }

    shouldDisplay = (result) => {
        if (this.searchValue && (
            !result.title.toLocaleLowerCase().includes(this.searchValue.toLocaleLowerCase()) &&
            !result.description.toLocaleLowerCase().includes(this.searchValue.toLocaleLowerCase())
        )) {
            return false;
        }

        if (this.searchType !== "all" && (
            this.searchType !== result.type
        )) {
            return false;
        }
        return true;
    }

    render() {
        return x`
            <section>
                <iai-silver-panel>
                    <div slot="content">
                        <div class="inputs">
                            <div class="group">
                                <iai-silver-select-input
                                    .inputId=${"search-mode"}
                                    .name=${"search-mode"}
                                    .label=${"Search:"}
                                    .hideLabel=${false}
                                    .value=${this.searchMode}
                                    .options=${[
                                        { value: "keyword", text: "Keyword" },
                                        { value: "semantic", text: "Semantic" },
                                    ]}
                                    .handleChange=${(e) => this.searchMode = e.target.value}
                                    .horizontal=${true}
                                ></iai-silver-select-input>

                                <iai-silver-select-input
                                    .inputId=${"search-type"}
                                    .name=${"search-type"}
                                    .label=${"Show:"}
                                    .hideLabel=${false}
                                    .value=${this.searchType}
                                    .options=${[
                                        { value: "all", text: "All Types" },
                                        { value: "question", text: "Questions" },
                                        { value: "response", text: "Responses" },
                                    ]}
                                    .handleChange=${(e) => this.searchType = e.target.value}
                                    .horizontal=${true}
                                ></iai-silver-select-input>
                            </div>

                            <div class="group">
                                <iai-icon-button
                                    title="Search settings"
                                    @click=${() => this._settingsVisible = !this._settingsVisible}
                                >
                                    <iai-icon
                                        slot="icon"
                                        name="settings"
                                        .color=${this._settingsVisible ? "var(--iai-silver-color-dark)" : "var(--iai-silver-color-text)"}
                                        .fill=${1}
                                    ></iai-icon>
                                </iai-icon-button>

                                <div class="popup" style=${`opacity: ${this._settingsVisible ? 1 : 0}; pointer-events: ${this._settingsVisible ? "auto" : "none"};`}>
                                    <iai-silver-title
                                        .text=${"Search Settings"}
                                        .variant=${"secondary"}
                                    ></iai-silver-title>
                                    <div style="display: flex; align-items: center; gap: 1em;">
                                        <iai-toggle-input
                                            style="margin-top: 1em;"
                                            name=${"highligh-matches"}
                                            .handleChange=${(e) => {
                                                console.log(e.target.value);
                                                this.searchHighlight = !this.searchHighlight;
                                            }}
                                            inputId=${"highligh-matches-toggle"}
                                            label=${"Highlight Matches"}
                                            value=${this.searchHighlight}
                                            .checked=${this.searchHighlight}
                                        ></iai-toggle-input>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <iai-silver-search-box
                            .inputId=${"default-search"}
                            .name=${"default-search"}
                            .label=${"Search"}
                            .placeholder=${this.searchMode == "keyword"
                                ? "Search by keywords in questions, themes or descriptions..."
                                : "Search by concepts like 'pollution sources', 'health effects', 'solutions'..."
                            }
                            .value=${this.searchValue}
                            .handleInput=${(e) => this.searchValue = e.target.value.trim()}
                        ></iai-silver-search-box>

                        ${this.searchMode === "semantic"
                            ? x`
                                <div class="info">
                                    <iai-icon
                                        .name=${"wand_stars"}
                                    ></iai-icon>
                                    <small>AI understands the meaning of your search</small>
                                </div>
                            `
                            : ""
                        }

                        <ul class="results-list">
                            ${this.results
                                .filter(result => this.shouldDisplay(result))
                                .map(result => x`
                                    <li>
                                        <iai-silver-cross-search-card
                                            .type=${result.type}
                                            .title=${result.title}
                                            .description=${result.description}
                                            .tags=${["test tag 1", "test tag 2","test tag 1 test tag 1 test tag 1", "test tag 2","test tag 1", "test tag 2","test tag 1", "test tag 2","test tag 1", "test tag 2","test tag 1 test tag 1", "test tag 2","test tag 1", "test tag 2"]}
                                            .highlightText=${this.searchHighlight ? this.searchValue : ""}
                                        ></iai-silver-cross-search-card>
                                    </li>
                                `)
                            }
                        </ul>
                    </div>
                </iai-silver-panel>
            </section>
        `
    }
}
customElements.define("iai-silver-cross-search", CrossSearch);

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

class DemographicsCard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        data: { type: Object }, //  key/value pairs
        _totalCount: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-demographics-card article {
                height: 100%;
                max-height: 40em;
                overflow: auto;
                padding: 1em;
                font-size: 1em;
                color: var(--iai-silver-color-text);
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
            }
            iai-demographics-card ul {
                display: flex;
                flex-direction: column;
                gap: 1.5em;
                margin: 0;
                padding-left: 0;
                font-weight: bold;
                font-size: 0.9em;
            }
            iai-demographics-card li {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-direction: column;
                list-style: none;
                line-height: 1.5em;
                gap: 0.5em;
            }
            iai-demographics-card li>* {
                width: 100%;
                word-wrap: break-word;
            }
            iai-demographics-card li .percentage {
                font-size: 0.8em;
                color: rgba(0, 0, 0, 0.5);
            }
            iai-demographics-card li .count {
                font-size: 1.2em;
            }
            iai-demographics-card li {
                font-size: 0.9em;
                color: rgba(0, 0, 0, 0.6);
            }
            iai-demographics-card .info {
                display: flex;
                gap: 0.5em;
            }
            iai-demographics-card .label {
                font-size: 0.9em;
            }
            iai-demographics-card .counts {
                display: flex;
                align-items: center;
                gap: 1em;
                font-weight: normal;
                font-size: 0.8em;
            }
            
            iai-demographics-card iai-silver-progress-bar .container,
            iai-demographics-card iai-silver-progress-bar .container .bar {
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
        
        this.applyStaticStyles("iai-demographics-card", DemographicsCard.styles);
    }

    updated(changedProps) {
        if (changedProps.has("data")) {
            this._totalCount = Object.values(this.data).reduce( (a, b) => a + b, 0 );
        }
    }

    render() {
        return x`
            <article>
                <iai-silver-title
                    .text=${this.title}
                    .level=${3}
                ></iai-silver-title>

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
customElements.define("iai-demographics-card", DemographicsCard);

class DemographicsSection extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
        themeFilters: { type: Array },
        demoFilters: { type: Object},
        total: { type: Number },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4` 
            iai-demographics-section .cards {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                max-width: 100%;
                overflow: auto;
            }    
            iai-demographics-section iai-demographics-card {
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
        this.data = [];
        this.themeFilters = [];
        this.demoFilters = {};
        this.total = 0;

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};
        
        this.applyStaticStyles("iai-demographics-section", DemographicsSection.styles);
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
                            .text=${"Demographics"}
                            .subtext=${"Demographic breakdown for this question"}
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
                                        <iai-demographics-card
                                            .title=${this.toTitleCase(category)}
                                            .data=${this.data[category]}
                                        ></iai-demographics-card>
                                    ` : ""})}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-demographics-section", DemographicsSection);

class ResponseRefinement extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: { type: Array },
        highlightMatches: { type: Boolean },
        demoData: { type: Object },
        demoOptions: { type: Object },
        themes: { type: Array },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },

        searchValue: { type: String },
        setSearchValue: { type: Function },

        searchMode: { type: Boolean },
        setSearchMode: { type: Function },

        evidenceRich: { type: Boolean },
        setEvidenceRich: { type: Function },

        highlightMatches: { type: Boolean },
        setHighlightMatches: { type: Function },

        demoFilters: { type: Object },
        setDemoFilters: { type: Function },

        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },

        _settingsVisible: { type: Boolean },
        _themeFiltersVisible: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-response-refinement label,
            iai-response-refinement select,
            iai-response-refinement input {
                font-size: 0.9em !important;
            }
            iai-response-refinement .filters {
                display: flex;
                gap: 1em;
                width: 100%;
                flex-direction: column;
            }
            iai-response-refinement iai-silver-select-input {
                display: block;
                width: max-content;
            }
            iai-response-refinement .search-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5em;
            }
            iai-response-refinement .search-container iai-silver-search-box {
                flex-grow: 1;
            }
            iai-response-refinement .search-container iai-silver-search-box .clear-button {
                top: 70%;
            }
            iai-response-refinement iai-silver-tag .material-symbols-outlined {
                font-size: 2em;
            }
            iai-response-refinement .tag {
                width: 100%;
            }
            iai-response-refinement input[type="checkbox"] {
                width: auto;
                filter: grayscale(0.5) hue-rotate(75deg);
                cursor: pointer;
            },
            iai-response-refinement label {
                cursor: pointer;
                white-space: nowrap;
            }
            iai-response-refinement .filters-row {
                display: flex;
                align-items: flex-end;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-response-refinement .theme-filter-list {
                list-style: none;
                padding-left: 0;
                margin: 0;
            }
            iai-response-refinement .theme-filter-list li {
                display: flex;
                gap: 0.5em;
                justify-content: flex-start;
                margin-bottom: 0.5em;
            }
            iai-response-refinement iai-silver-select-input .govuk-form-group {
                margin-bottom: 0;
            }
            iai-response-refinement iai-theme-filters-warning {
                width: 100%;
            }
            iai-response-refinement .popup-button .popup-panel {
                position: absolute;
                top: 2em;
                width: max-content;
                right: 0;
                background: white;
                padding: 1em;
                margin: 0;
                z-index: 2;
                border: 1px solid var(--iai-silver-color-mid);
                border-radius: 0.5em;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
                box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
            }
            iai-response-refinement .popup-button {
                position: relative;
            }
            iai-response-refinement .popup-button .popup-panel.themes-panel {
                right: unset;
                left: 0;
            }
            iai-response-refinement .popup-panel .content {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-response-refinement .popup-button .icon-container {
                margin-bottom: 0.5em;
            }
            iai-response-refinement .popup-button iai-silver-title {
                color: var(--iai-silver-color-dark);
                cursor: pointer;
            }
            iai-response-refinement .popup-button .popup-button__body {
                position: relative;
            }
            iai-response-refinement .popup-button .popup-button__body iai-silver-button button {
                line-height: 2em;
                background: var(--iai-silver-color-light);
                border: none;
                border-radius: 0.3em;
            }
            iai-response-refinement .popup-button .popup-button__text {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.demoData = {};
        this.demoOptions = {};
        this.themes = [];

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};

        this.searchValue = "";
        this.setSearchValue = () => {};

        this.searchMode = "keyword";
        this.setSearchMode = () => {};

        this.highlightMatches = true;
        this.setHighlightMatches = () => {};

        this.evidenceRich = false;
        this.setEvidenceRich = () => {};

        this.demoFilters = {};
        this.setDemoFilters = () => {};

        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this._settingsVisible = false;
        this._themeFiltersVisible = false;
        
        this.applyStaticStyles("iai-response-refinement", ResponseRefinement.styles);
    }

    handleThemeFiltersBlur = (e) => {
        if (!document.getElementById("theme-filters-panel").contains(e.target)) {
            this._themeFiltersVisible = false;
        }
    }

    handleSettingsBlur = (e) => {
        if (!document.getElementById("settings-panel").contains(e.target)) {
            this._settingsVisible = false;
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.setupPanelListeners(window.addEventListener);    }

    disconnectedCallback() {
        this.setupPanelListeners(window.removeEventListener);
        super.disconnectedCallback();
    }

    setupPanelListeners = (func) => {
        [this.handleSettingsBlur].forEach(eventHandler => {
            ["click", "touchstart"].forEach(eventName => {
                func(eventName, eventHandler);
            });
        });
    }

    render() {
        return x`
            <iai-silver-panel>
                <div slot="content">
                    <iai-silver-title
                        .level=${2}
                        .text=${`Response refinement`}
                        .subtext=${"Filter and search through individual responses to this question."}
                        .icon=${"filter_alt"}
                        .aside=${x`
                            ${this.demoFiltersApplied() || this.themeFiltersApplied() ? x`
                                <iai-silver-button
                                    .text=${"Clear filters"}
                                    .handleClick=${() => {
                                        this.updateThemeFilters();
                                        this.setDemoFilters();
                                    }}
                                ></iai-silver-button>
                            ` : ""}
                        `}
                    ></iai-silver-title>

                    <div class="filters">
                        <iai-silver-select-input
                            .inputId=${"search-mode"}
                            .name=${"search-mode"}
                            .label=${"Search:"}
                            .hideLabel=${false}
                            .value=${this.searchMode}
                            .options=${[
                                { value: "keyword", text: "Keyword" },
                                { value: "semantic", text: "Semantic" },
                            ]}
                            .handleChange=${(e) => this.setSearchMode(e.target.value)}
                            .horizontal=${true}
                        ></iai-silver-select-input>

                        ${this.searchMode === "semantic" ? x`
                            <iai-silver-tag
                                .status=${"Open"}
                                .icon=${"network_intelligence"}
                                .text=${"Semantic search uses AI to understand the meaning behind your search terms, finding responses with similar concepts even if they don't contain the exact words."}
                            ></iai-silver-tag>
                        ` : ""}

                        <div class="search-container">
                            <iai-silver-search-box
                                .inputId=${"search-value"}
                                .name=${"search-value"}
                                .label=${"Search"}
                                .placeholder=${this.searchMode == "keyword"
                                    ? "Search by keywords in questions, themes or descriptions..."
                                    : "Search by concepts like 'pollution sources', 'health effects', 'solutions'..."
                                }
                                .value=${this.searchValue}
                                .handleInput=${(e) => this.setSearchValue(e.target.value.trim())}
                            ></iai-silver-search-box>

                            <div id="settings-panel" class="popup-button">
                                <div class="popup-button__body">
                                    <iai-icon-button
                                        title="Search settings"
                                        @click=${() => this._settingsVisible = !this._settingsVisible}
                                    >
                                        <iai-icon
                                            slot="icon"
                                            name="settings"
                                            .color=${this._settingsVisible ? "var(--iai-silver-color-dark)" : "var(--iai-silver-color-text)"}
                                            .fill=${1}
                                        ></iai-icon>
                                    </iai-icon-button>

                                    <div class="popup-panel" style=${`
                                        opacity: ${this._settingsVisible ? 1 : 0};
                                        pointer-events: ${this._settingsVisible ? "auto" : "none"};
                                    `}>
                                        <iai-silver-title
                                            .text=${"Search Settings"}
                                            .variant=${"secondary"}
                                        ></iai-silver-title>
                                        <div class="content">
                                            <iai-toggle-input
                                                name=${"highligh-matches"}
                                                .handleChange=${(e) => {
                                                    this.setHighlightMatches(!this.highlightMatches);
                                                }}
                                                inputId=${"highligh-matches-toggle"}
                                                label=${"Highlight Matches"}
                                                value=${this.highlightMatches}
                                                .checked=${this.highlightMatches}
                                            ></iai-toggle-input>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div >
                            <iai-toggle-input
                                name=${"evidence-rich"}
                                .handleChange=${(e) => {
                                    this.setEvidenceRich(!this.evidenceRich);
                                }}
                                inputId=${"evidence-rich-input"}
                                label=${"Evidence-rich responses"}
                                value=${this.evidenceRich}
                                .checked=${this.evidenceRich}
                            ></iai-toggle-input>
                        </div>
                        
                        <div class="filters-row">
                            ${Object.keys(this.demoOptions).map(key => x`
                                <iai-multi-dropdown
                                    .title=${this.toTitleCase(key)}
                                    .text=${`${this.demoFilters[key]?.length || 0} filters selected`}
                                    .options=${this.demoOptions[key].map(option => ({
                                        id: option,
                                        checked: Boolean(this.demoFilters[key]?.includes(option)),
                                        title: option,
                                        handleClick: (e) => {
                                            this.setDemoFilters(key, e.target.value);
                                        },
                                    }))}
                                ></iai-multi-dropdown>
                            `)}
                        </div>

                        <div class="filters-row">
                            <iai-multi-dropdown
                                .title=${"Themes"}
                                .text=${`${this.themeFilters.length} themes selected`}
                                .options=${this.themes.map(theme => ({
                                    id: theme.id,
                                    checked: this.themeFilters.includes(theme.id),
                                    title: theme.title,
                                    handleClick: (e) => {
                                        this.updateThemeFilters(theme.id);
                                    },
                                }))}
                            ></iai-multi-dropdown>
                        </div>

                        <div class="filters-row">
                            ${this.themeFilters.length > 0 ? x`
                                <iai-theme-filters-warning
                                    .themes=${this.themes}
                                    .themeFilters=${this.themeFilters}
                                    .updateThemeFilters=${this.updateThemeFilters}
                                ></iai-theme-filters-warning>
                            ` : ""}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-response-refinement", ResponseRefinement);

class ResponsesList extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: { type: Array },
        responsesTotal: { type: Number },
        filteredTotal: { type: Number },
        handleScrollEnd: { type: Function },
        isLoading: { type: Boolean },
        highlightedText: { type: String },
        handleThemeTagClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-silver-responses-list ul {
                padding-left: 0;
            }
            iai-silver-responses-list li {
                list-style: none;
            }
            iai-silver-responses-list article {
                display: flex;
                flex-direction: column;
                gap: 1em;
                width: 100%;
                margin-block: 1em;
                padding: 1em;
                line-height: 1.5em;
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
            }
            iai-silver-responses-list article p {
                margin: 0;
            }
            iai-silver-responses-list article .demo-tag {
                max-width: 100%;
            }
            iai-silver-responses-list article .theme-tag button {
                text-align: start;
            }
            iai-silver-responses-list article header,
            iai-silver-responses-list article footer {
                display: flex;
                align-items: center;
                gap: 0.5em;
                font-size: 0.9em;
                flex-wrap: wrap;
            }
            iai-silver-responses-list article header {
                justify-content: space-between;
            }
            iai-silver-responses-list article header .header-group {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.5em;
            }
            iai-silver-responses-list article footer iai-silver-tag .tag {
                background: var(--iai-silver-color-mid-light);
                border: none;
            }
            iai-silver-responses-list iai-virtual-list {
                height: 50em;
            }
            iai-silver-responses-list multi-answers-list {
                display: flex;
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.responses = [];
        this.responsesTotal = 0;
        this.filteredTotal = 0;
        this.handleScrollEnd = () => {};
        this.isLoading = false;
        this.highlightedText = "";
        this.handleThemeTagClick = () => {};
        
        this.applyStaticStyles("iai-silver-responses-list", ResponsesList.styles);
    }

    render() {
        return x`
            <iai-silver-panel>
                <div slot="content">
                    <iai-silver-title
                        .text=${`Responses (${this.filteredTotal})`}
                        .subtext=${"All responses to this question"}
                        .level=${2}
                    ></iai-silver-title>

                    <iai-virtual-list
                        style=${this.isLoading && this.responses.length === 0
                            ? "height: auto;"
                            : ""
                        }
                        .data=${this.responses}
                        .renderItem=${(response, index) => x`
                            <article class=${index === this.responses.length-1
                                ? "last-item"
                                : ""
                            }>
                                <header>
                                    ${response.demoData.length > 0 || response.evidenceRich ? x`
                                        <div class="header-group">
                                            ${response.demoData
                                                ? response.demoData.map(data => x`
                                                    <iai-silver-tag
                                                        class="demo-tag"
                                                        .text=${data}
                                                    ></iai-silver-tag>
                                                `)
                                                : ""
                                            }
                                            ${response.evidenceRich
                                                ? x`
                                                    <iai-silver-tag
                                                        .icon=${"diamond"}
                                                        .text=${"Evidence rich"}
                                                        .status=${"Closed"}
                                                    ></iai-silver-tag>
                                                `
                                                : ""
                                            }
                                        </div>
                                    ` : ""}

                                    <small>
                                        ID: ${response.id || "Not Available"}
                                    </small>
                                </header>
                                
                                ${response.text ? x`
                                    <p>
                                        ${this.highlightedText
                                            ? o$2(this.getHighlightedText(response.text, this.highlightedText))
                                            : response.text
                                        }
                                    </p>
                                ` : ""}

                                ${response.multiAnswers.length > 0 ? x`
                                    <ul class="multi-answers-list">
                                        ${response.multiAnswers.map(answer => x`
                                            <iai-silver-tag
                                                .text=${answer}
                                            ></iai-silver-tag>
                                        `)}
                                    </ul>
                                ` : ""}
                                
                                ${response.themes.length > 0 ? x`
                                    <footer>
                                        <small>
                                            Themes:
                                        </small>
                                        ${response.themes.map((theme) => x`
                                            <iai-silver-button
                                                class="theme-tag"
                                                @click=${() => this.handleThemeTagClick(theme.id)}
                                                .text=${theme.text}
                                            ></iai-silver-button>
                                        `)}
                                    </footer>
                                ` : ""}
                            </article>
                        `}
                        .handleScrollEnd=${this.handleScrollEnd}
                    ></iai-virtual-list>

                    ${this.isLoading
                        ? x`<iai-loading-indicator></iai-loading-indicator>`
                        : ""
                    }
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-responses-list", ResponsesList);

class QuestionDetailPage extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,

        _activeTab: { type: String },
        _isLoading: { type: Boolean },
        _currentPage: { type: Number},
        _hasMorePages: { type: Boolean},
        _errorOccured: { type: Boolean},
        fetchData: { type: Function },
        _isFavourited: { type: Boolean},

        consultationSlug: { type: String },
        questionSlug: { type: String },
        consultationTitle: { type: String},
        questionText: { type: String},
        questionId: { type: String },

        responses: { type: Array },
        _responsesTotal: { type: Number },
        _filteredTotal: { type: Number },
        _themes: { type: Array },
        _demoData: { type: Object },
        _demoOptions: { type: Object },

        _searchValue: { type: String },
        _searchMode: { type: String },
        _highlightMatches: { type: Boolean },
        _evidenceRichFilter: { type: Boolean },
        _themeFilters: { type: Array },
        _demoFilters: { type: Object },

        _themesSortType: { type: String },
        _themesSortDirection: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        i$4`
            iai-question-detail-page {
                color: var(--iai-silver-color-text);
            }
            iai-question-detail-page select,
            iai-question-detail-page input {
                width: 100%;
            }
            iai-question-detail-page section {
                margin-bottom: 1em;
            }
            iai-question-detail-page section.breadcrumbs {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1em;
            }
            iai-question-detail-page section.breadcrumbs iai-silver-button button {
                display: flex;
                gap: 0.5em;
                align-items: center;
                justify-content: space-between;
            }
            iai-question-detail-page .response-total {
                display: flex;
                align-items: center;
            }
            iai-question-detail-page iai-icon-button {
                margin-top: -0.4em;
            }
            iai-question-detail-page .load-more-button {
                margin-top: 1em;
                display: flex;
                justify-content: center;
            }
            @media screen and (max-width: 500px) {
                iai-question-detail-page section.breadcrumbs {
                    justify-content: center;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this._MAX_THEME_FILTERS = Infinity;
        this._PAGE_SIZE = 50;
        this._DEBOUNCE_DELAY = 500;
        this._TAB_INDECES = {
            "Question Summary" : 0,
            "Response Analysis" : 1,
        };
        this._currentFetchController = null;

        // Prop defaults
        this._activeTab = this._TAB_INDECES["Question Summary"];
        this._isLoading = false;
        this._currentPage = 1;
        this._hasMorePages = true;
        this._errorOccured = false;
        this.fetchData = window.fetch.bind(window);
        this._isFavourited = false;

        this.consultationSlug = "";
        this.questionSlug = "";
        this.consultationTitle = "";
        this.questionText = "";
        this.questionId = "";

        this.responses = [];
        this._responsesTotal = 0;
        this._filteredTotal = 0;
        this._themes = [];
        this._demoData = {};
        this._demoOptions = {};
        
        this._searchValue = "";
        this._searchMode = "keyword";
        this._highlightMatches = true;
        this._evidenceRichFilter = false;
        this._themeFilters = [];
        this._demoFilters = {};

        this._themesSortType = "frequency"; // "frequency" | "alphabetical"
        this._themesSortDirection = "descending"; // "ascending" | "descending"

        this.applyStaticStyles("iai-question-detail-page", QuestionDetailPage.styles);
    }

    updateThemeFilters = (newFilter) => {
        if (!newFilter) {
            // Clear filters if newFilter is falsy
            this._themeFilters = [];
            return;
        }
        if (this._themeFilters.includes(newFilter)) {
            this._themeFilters = [...this._themeFilters.filter(filter => filter !== newFilter)];
        } else {
            if (this._themeFilters.length === this._MAX_THEME_FILTERS) {
                this._themeFilters = [...this._themeFilters.slice(1), newFilter];
            } else {
                this._themeFilters = [...this._themeFilters, newFilter];
            }
        }
    }

    buildQuery = () => {
        // conditionally add filters as query params
        const params = new URLSearchParams({
            ...(this._searchValue && {
                searchValue: this._searchValue
            }),
            ...(this._themeFilters.length > 0 && {
                themeFilters: this._themeFilters.join(",")
            }),
            ...(this._searchMode && {
                searchMode: this._searchMode
            }),
            ...(this._evidenceRichFilter && {
                evidenceRich: this._evidenceRichFilter
            }),
            ...(this._themesSortType && {
                themesSortType: this._themesSortType
            }),
            ...(this._themesSortDirection && {
                themesSortDirection: this._themesSortDirection
            }),
            page: this._currentPage,
            page_size: this._PAGE_SIZE.toString(),
        });

        // Filter out demo filter keys with no value
        const validDemoFilterKeys = Object.keys(this._demoFilters).filter(key => Boolean(this._demoFilters[key]));
        // Add each demo filter as a duplicate demoFilter param
        for (const key of validDemoFilterKeys) {
            const filterArr = this._demoFilters[key];
            if (filterArr && filterArr.length > 0) {
                // TODO: Replace below with the commented out code after the back end is implemented.
                // Only processing the first filter for now to avoid breaking back end responses.
                // params.append("demoFilters", `${key}:${filterArr.join(",")}`);
                params.append("demoFilters", `${key}:${filterArr[0]}`);
            }
        }

        return params.toString();
    }

    fetchResponses = async () => {
        clearTimeout(this._searchDebounceTimer);

        this._searchDebounceTimer = setTimeout(async () => {
            if (!this._hasMorePages) {
                return;
            }

            if (this._currentFetchController) {
                console.log("aborting stale request");
                this._currentFetchController.abort();
            }

            const controller = new AbortController();
            const signal = controller.signal;
            this._currentFetchController = controller;

            this._errorOccured = false;
            this._isLoading = true;

            const url = `/consultations/${this.consultationSlug}/responses/${this.questionSlug}/json?` + this.buildQuery();

            let response;
            try {
                response = await this.fetchData(url, { signal });
            } catch (err) {
                if (err.name == "AbortError") {
                    console.log("stale request aborted");
                    return;
                } else {
                    console.error(err);
                    this._errorOccured = true;
                    return;
                }
            } finally {
                if (this._currentFetchController === controller) {
                    this._currentFetchController = null;
                }
                this._isLoading = false;
            }

            if (!response.ok) {
                this._errorOccured = true;
                throw new Error(`Response status: ${response.status}`);
            }

            const responsesData = await response.json();

            this.responses = this.responses.concat(responsesData.all_respondents);

            this._responsesTotal = responsesData.respondents_total;
            this._filteredTotal = responsesData.filtered_total;

            this._themes = responsesData.theme_mappings.map(mapping => ({
                id: mapping.value,
                title: mapping.label,
                description: mapping.description,
                mentions: parseInt(mapping.count),
                handleClick: () => {
                    this._themeFilters = [mapping.value];
                    this._activeTab = this._TAB_INDECES["Response Analysis"];
                }
            }));

            this._demoData = responsesData.demographic_aggregations || {};
            this._demoOptions = responsesData.demographic_options || {};

            // Update theme mappings only on first page (when _currentPage === 1) to reflect current filters
            if (this._currentPage === 1 && responsesData.theme_mappings) {
                this.themeMappings = responsesData.theme_mappings;
            }

            this._hasMorePages = responsesData.has_more_pages;

            this._currentPage = this._currentPage + 1;
        }, this._DEBOUNCE_DELAY);
    }

    resetResponses = () => {
        this.responses = [];
        this._currentPage = 1;
        this._hasMorePages = true;
        this._isLoading = true;
    }

    demoFiltersApplied = () => {
        for (const key of Object.keys(this._demoFilters)) {
            const filterArr = this._demoFilters[key];

            // filterArr can be undefined or empty array
            if (filterArr && filterArr.filter(Boolean).length > 0) {
                return true;
            }
        }
        return false;
    }

    themeFiltersApplied = () => {
        return this._themeFilters.length > 0;
    }

    setDemoFilters = (newFilterKey, newFilterValue) => {
        if (!newFilterKey || !newFilterValue) {
            // Clear filters if nothing is passed
            this._demoFilters = {};
            return;
        }

        const existingFilters = this._demoFilters[newFilterKey] || [];

        let resultFilters;
        if (existingFilters.includes(newFilterValue)) {
            // Remove filter if already added
            resultFilters = existingFilters.filter(filter => newFilterValue !== filter);
        } else {
            // Avoid duplicates when adding filters
            resultFilters = [...new Set([...existingFilters, newFilterValue])];
        }

        this._demoFilters = {
            ...this._demoFilters,
            [newFilterKey]: resultFilters,
        };
    }

    firstUpdated() {
        this._isFavourited = this.isFavourited();
    }

    updated(changedProps) {
        if (
            changedProps.has("_searchValue")        ||
            changedProps.has("_searchMode")         ||
            changedProps.has("_evidenceRichFilter") ||
            changedProps.has("_themeFilters")       ||
            changedProps.has("_demoFilters")        ||
            changedProps.has("_themesSortType")     ||
            changedProps.has("_themesSortDirection")
        ) {
            this.resetResponses();
            this.fetchResponses();
        }
    }

    isFavourited() {
        return this.getStoredValues(this._STORAGE_KEYS.FAVOURITE_QUESTIONS).includes(this.questionId);
    }

    renderThemeAnalysisSection = () => {
        return x`
            <section>
                <iai-demographics-section
                    .data=${this._demoData}
                    .themeFilters=${this._themeFilters}
                    .demoFilters=${this._demoFilters}
                    .demoFiltersApplied=${this.demoFiltersApplied}
                    .themeFiltersApplied=${this.themeFiltersApplied}
                    .total=${this._filteredTotal}
                ></iai-demographics-section>
            </section>
            
            <section class="theme-analysis">
                <iai-theme-analysis
                    .consultationSlug=${this.consultationSlug}
                    .themes=${this._themes}
                    .demoData=${this._demoData}
                    .demoOptions=${this._demoOptions}
                    .totalResponses=${this._filteredTotal}

                    .demoFiltersApplied=${this.demoFiltersApplied}
                    .themeFiltersApplied=${this.themeFiltersApplied}

                    .themeFilters=${this._themeFilters}
                    .updateThemeFilters=${this.updateThemeFilters}
                    
                    .sortType=${this._themesSortType}
                    .setSortType=${newSortType => this._themesSortType = newSortType}

                    .sortDirection=${this._themesSortDirection}
                    .setSortDirection=${newSortDirection => this._themesSortDirection = newSortDirection}

                    .demoFilters=${this._demoFilters}
                    .setDemoFilters=${this.setDemoFilters}
                ></iai-theme-analysis>
            </section>
        `
    }

    renderResponsesSection = () => {
        return x`
            <section>
                <iai-response-refinement
                    .demoData=${this._demoData}
                    .demoOptions=${this._demoOptions}
                    .themes=${this._themes}

                    .demoFiltersApplied=${this.demoFiltersApplied}
                    .themeFiltersApplied=${this.themeFiltersApplied}

                    .searchValue=${this._searchValue}
                    .setSearchValue=${newSearchValue => this._searchValue = newSearchValue}

                    .searchMode=${this._searchMode}
                    .setSearchMode=${newSearchMode => this._searchMode = newSearchMode}

                    .evidenceRich=${this._evidenceRichFilter}
                    .setEvidenceRich=${newEvidenceRich => this._evidenceRichFilter = newEvidenceRich}

                    .highlightMatches=${this._highlightMatches}
                    .setHighlightMatches=${newHighlightMatches => this._highlightMatches = newHighlightMatches}

                    .demoFilters=${this._demoFilters}
                    .setDemoFilters=${this.setDemoFilters}

                    .themeFilters=${this._themeFilters}
                    .updateThemeFilters=${this.updateThemeFilters}
                ></iai-response-refinement>
            </section>

            <section>
                <iai-silver-responses-list
                    .responses=${
                        this.responses.map(response => ({
                            id: response.identifier,
                            text: response.free_text_answer_text,
                            themes: response.themes.map(theme => ({
                                id: theme.id,
                                text: theme.name,
                            })),
                            evidenceRich: response.evidenceRich,
                            multiAnswers: response.multiple_choice_answer || [],
                            demoData: Object.values(response.demographic_data) || [],
                        }))
                    }
                    .handleScrollEnd=${() => {
                        // // Uncomment to enable infinite scroll
                        // if (this._isLoading) {
                        //     return;
                        // }
                        // this.fetchResponses();
                    }}
                    .responsesTotal=${this._responsesTotal}
                    .filteredTotal=${this._filteredTotal}
                    .isLoading=${this._isLoading}
                    .highlightedText=${this._highlightMatches ? this._searchValue : ""}
                    .handleThemeTagClick=${(themeId) => {
                        this.updateThemeFilters(themeId);
                        this._activeTab = this._TAB_INDECES["Question Summary"];
                    }}
                ></iai-silver-responses-list>

                ${this._hasMorePages ? x`
                    <iai-silver-button
                        class="load-more-button"
                        .text=${`Load more (${this._filteredTotal - this.responses.length} remaining)`}
                        .handleClick=${() => {
                            if (this._isLoading) {
                                return;
                            }
                            this.fetchResponses();
                        }}
                    ></iai-silver-button>`
                : ""}
            </section>
        `
    }

    renderTabButton = (text, icon) => {
        return x`
            <iai-icon
                .name=${icon}
            ></iai-icon>
            <span>
                ${text}
            </span>
        `
    }

    render() {
        return x`
            <section class="breadcrumbs">
                <iai-silver-button
                    .text=${x`
                        <iai-icon
                            .name=${"chevron_left"}
                            .color=${"var(--iai-silver-color-text)"}
                        ></iai-icon>
                        <span>Back to all questions</span>
                    `}
                    .handleClick=${() => window.location.href = `/consultations/${this.consultationSlug}/`}
                ></iai-silver-button>

                <small>
                    Choose a different question to analyse
                </small>
            </section>

            <section class="question-title">
                <iai-silver-cross-search-card
                    .type=${"question"}
                    .title=${this.questionText}
                    .aside=${x`
                        <iai-icon-button
                            class="favourite-button"
                            title="Favourite this question"
                            @click=${(e) => {
                                e.stopPropagation();
                                this.toggleStorage(
                                    this.questionId,
                                    this._STORAGE_KEYS.FAVOURITE_QUESTIONS
                                );
                                this._isFavourited = this.isFavourited();
                            }}
                        >
                            <iai-icon
                                slot="icon"
                                name="star"
                                .color=${"var(--iai-silver-color-text)"}
                                .fill=${this._isFavourited ? 1 : 0}
                            ></iai-icon>
                        </iai-icon-button>
                    `}
                    .footer=${x`
                        <small class="response-total">
                            ${this._responsesTotal.toLocaleString()} responses
                        </small>
                        <iai-silver-tag
                            .status=${"Open"}
                            .text=${"Open"}
                            .icon=${"chat_bubble"}
                        ></iai-silver-tag>
                    `}
                ></iai-silver-cross-search-card>
            </section>

            <iai-tab-view
                .activeTab=${this._activeTab}
                .handleTabChange=${(newTab) => this._activeTab = newTab}
                .tabs=${[
                    {
                        title: this.renderTabButton("Question summary", "lan"),
                        content: this.renderThemeAnalysisSection()
                    },
                    {
                        title: this.renderTabButton("Response analysis", "finance"),
                        content: this.renderResponsesSection()
                    },
                ]}
            ></iai-tab-view>
        `
    }
}
customElements.define("iai-question-detail-page", QuestionDetailPage);
//# sourceMappingURL=index.js.map
