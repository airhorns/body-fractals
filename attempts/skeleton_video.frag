uniform vec2 resolution;
uniform sampler2D frame;


void main()
{
  vec2 p = gl_FragCoord.xy / resolution.xy;
  gl_FragColor = vec4(texture2D(frame, p).aaa * 15.0, 1.0);
}
