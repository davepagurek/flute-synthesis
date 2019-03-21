class Slide {
  constructor(node) {
    this.node = node;
    this.maxOrder = 0;
    this.order = 0;
    Array.from(node.querySelectorAll('*')).forEach(child => {
      const order = child.getAttribute('data-order');
      if (order) {
        this.maxOrder = Math.max(this.maxOrder, parseInt(order));
      }

      const disappear = child.getAttribute('data-disappear');
      if (disappear) {
        this.maxdisappear = Math.max(this.maxdisappear, parseInt(disappear));
      }

      if (child.classList.contains('disappearing')) {
        node.classList.add('unstretched');
        const style = child.getAttribute('style') || '';
        const oldStyle = node.getAttribute('style');
        node.setAttribute('style', 'display: block;');
        const width = child.getBoundingClientRect().width;
        const height = child.getBoundingClientRect().height;
        child.setAttribute(
          'style',
          `${style} max-width: ${width}px; max-height: ${height}px;`);
        node.setAttribute('style', oldStyle);
        node.classList.remove('unstretched');
      }
    });
  }

  // Resets the slide state and returns the DOMNode the slide will work in.
  show(fromStart) {
    if (fromStart) {
      this.order = 0;
    } else {
      this.order = this.maxOrder;
    }
    this.update();

    return this.node;
  }

  // Steps the current slide. Returns `true` if the slide was able
  // to step itself, and `false` if it had no more steps.
  increment() {
    if (this.order === this.maxOrder) {
      return false;

    } else {
      this.order++;
      this.update();

      return true;
    }
  }

  // Steps back the current slide. Returns `true` if the slide was able
  // to step itself, and `false` if it had no more steps.
  decrement() {
    if (this.order === 0) {
      return false;

    } else {
      this.order--;
      this.update();

      return true;
    }
  }

  update() {
    Array.from(this.node.querySelectorAll('*')).forEach(child => {
      const order = child.getAttribute('data-order');
      const disappear = child.getAttribute('data-disappear');
      const highlight = child.getAttribute('data-highlight');
      if (order || disappear) {
        if (!order || parseInt(order) <= this.order) {
          if (!disappear || disappear > this.order) {
            child.classList.remove('hidden');
          } else {
            child.classList.add('hidden');
          }
        } else {
          child.classList.add('hidden');
        }
      }
      if (highlight && parseInt(highlight) === this.order) {
        child.classList.add('highlighted');
      } else if (!child.classList.contains('fixed')) {
        child.classList.remove('highlighted');
      }
    });
  }
};

window.Slide = Slide;
