uniform vec2 triangleA;
uniform vec2 triangleB;
uniform vec2 triangleC;
uniform vec2 resolution;
uniform vec4 foregroundColor;
uniform vec4 backgroundColor;
uniform float tipColorSelector;


vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float sign(vec2 p1, vec2 p2, vec2 p3) {
    return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y);
}

bool PointInTriangle (vec2 pt) {
    bool b1, b2, b3;

    b1 = sign(pt, triangleA, triangleB) < 0.0;
    b2 = sign(pt, triangleB, triangleC) < 0.0;
    b3 = sign(pt, triangleC, triangleA) < 0.0;
    return ((b1 == b2) && (b2 == b3));
}

void main() {
  if (PointInTriangle(vec2(gl_FragCoord.x / resolution.x, gl_FragCoord.y / resolution.y))) {
    if ((gl_FragCoord.y / resolution.y) < (triangleC.y + 0.02)) {
      gl_FragColor = vec4(hsv2rgb(vec3(tipColorSelector, 0.8, 0.4)), 1.0);                                   
    } else {
      gl_FragColor = foregroundColor;
    }
  } else {
    gl_FragColor = backgroundColor;
  }
}
