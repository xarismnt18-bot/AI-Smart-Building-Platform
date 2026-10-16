import { Component } from "react";

/**
 * Skips an optional 3D layer (e.g. post-processing) if it fails to load,
 * instead of blanking the whole canvas.
 */
export class OptionalBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error) {
    console.warn("Optional 3D layer unavailable:", error.message);
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}
