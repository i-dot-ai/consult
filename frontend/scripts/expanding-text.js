//@ts-check


function split_on_space(text, search_start) {
  const split_point = text.indexOf(' ', search_start)

  if (split_point === -1) {
    return [text, '']
  } else {
    return [text.slice(0, split_point), text.slice(split_point)]
  }

}

// Expanding text
// NOTE: If there are likely to be multiple instances of this component on a page, each will need a unique accessible id
class ExpandingText extends HTMLElement{
  constructor() {
    super();
  }

  connectedCallback() {
    this.text_length = this.textContent?.length

    if (this.text_length && this.text_length > 450) {
      this.text_split = split_on_space(this.textContent, 400)
      this.display_text = this.text_split[0];
      this.hidden_text = this.text_split[1];

      if (this.hidden_text.length > 0) {
        this.innerHTML = `
          <span>${this.display_text}</span><span class="ellipsis">...</span><span class="hidden-text" style="display: none" id="hidden-text" tabindex="-1">${this.hidden_text}</span>
          <button class="expander" aria-expanded="false" aria-controls="hidden-text" class="govuk-button govuk-button--secondary" data-module="govuk-button">
            Read more
          </button>
          `
  
        this.ellipsis = /** @type HTMLElement */ (this.querySelector('.ellipsis'))
        this.hidden_text_element = /** @type HTMLElement */ (this.querySelector('.hidden-text'))
        this.expander = /** @type HTMLElement */ (this.querySelector('.expander'))
  
        this.expander?.addEventListener('click', () => {
          this.expanded = this.expander?.getAttribute('aria-expanded') === 'true'
          this.expander?.setAttribute('aria-expanded', String(!this.expanded))
          if (this.hidden_text_element && this.ellipsis) {
            this.hidden_text_element.style.display = this.expanded ? 'none' : 'block'
            this.ellipsis.style.display = this.expanded ? 'block' : 'none'

            if (this.expanded) {
              this.hidden_text_element.focus()
            }
          }
          if (this.expander) {
            this.expander.textContent = this.expanded ? 'Read more' : 'Read less'
          }
        })
      }

    }
  }

}

customElements.define('expanding-text', ExpandingText);