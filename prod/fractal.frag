uniform float time;
uniform vec2 resolution;
uniform vec3 cameraPos;
uniform vec3 cameraLookat;
uniform vec3 lightDir;
uniform vec3 diffuse;
uniform float ambientFactor;
uniform bool antialias;
uniform int distanceEstimatorFunction;
uniform float iterationScale;
uniform float iterationOffsetX;
uniform float iterationOffsetY;
uniform float iterationOffsetZ;
uniform float iterations;
uniform int trapFunction;
uniform float trapWidth;
uniform int colorTrapFunction;
uniform float angleA;
uniform float angleB;
uniform float angleC;

#define PI 3.14159265
#define GAMMA 0.8
#define AO_SAMPLES 5
#define RAY_DEPTH 256
#define MAX_DEPTH 100.0
#define SHADOW_RAY_DEPTH 32
#define DISTANCE_MIN 0.01

const vec2 delta = vec2(DISTANCE_MIN, 0.);


vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec3 RotateY(vec3 p, float a)
{
   float c,s;
   vec3 q=p;
   c = cos(a);
   s = sin(a);
   p.x = c * q.x + s * q.z;
   p.z = -s * q.x + c * q.z;
   return p;
}

vec2 rotate(vec2 v, float a) {
  return vec2(cos(a)*v.x + sin(a)*v.y, -sin(a)*v.x + cos(a)*v.y);
}

float trap(vec3 p){
  switch (trapFunction) {
    case 1: return length(p); // <- no trap
    case 2: return length(p.x-(trapWidth)); // <- cube forms
  }
  // return  length(p.x-1.0); // unit cube
  // return  length(p.x-0.5-0.5*sin(time/10.0)); // <- cube forms
  // return length(p.xz-vec2(1.0,1.0))-0.05; // <- tube forms
}

vec3 colorTrap(vec3 previousTrap, float iterationFactor, vec3 p) {
  switch (colorTrapFunction) {
    case 1: return min(previousTrap, p * iterationFactor); // channel wise distance from the axis
    case 2: return max(previousTrap, 1/p); // channel wise proximity to the axis
    case 3: return min(previousTrap, normalize(p));
    // case 4: return vec3(0.4, 0.2, 0.3);
  }
}

// from https://www.shadertoy.com/view/XsX3z7
float OctoKaleidoscopeIFS(in vec3 z, out vec3 trapDistance) {
  float pointDistance = 1000.0;
  trapDistance = vec3(1000.0, 1000.0, 1000.0);
  vec3 iterationOffset = vec3(iterationOffsetX, iterationOffsetY, iterationOffsetZ);

  for (int n = 0; n < iterations; n++) {
    z.xz = rotate(z.xz, angleA);
    // This is octahedral symmetry,
    // with some 'abs' functions thrown in for good measure.
    if (z.x+z.y<0.0) z.xy = -z.yx;
    z = abs(z);
    if (z.x+z.z<0.0) z.xz = -z.zx;
    z = abs(z);
    if (z.x-z.y<0.0) z.xy = z.yx;
    z = abs(z);
    if (z.x-z.z<0.0) z.xz = z.zx;
    z = (z*iterationScale - iterationOffset * (iterationScale-1.0));
    z.yz = rotate(z.yz, angleB);
    z.xy = rotate(z.xy, angleC);

    float iterationFactor = pow(iterationScale, -float(n+1));
    trapDistance = colorTrap(trapDistance, iterationFactor, z);
    pointDistance = min(pointDistance, trap(z) * iterationFactor);
  }
  return pointDistance;
}

float TetraKaleidoscopeIFS(in vec3 z, out vec3 trapDistance) {
  float pointDistance = 1000.0;
  trapDistance = vec3(1000.0, 1000.0, 1000.0);
  vec3 iterationOffset = vec3(iterationOffsetX, iterationOffsetY, iterationOffsetZ);

  for (int n = 0; n < iterations; n++) {
    z.xz = rotate(z.xz, angleA);
    // Tetrahedral symmetry from http://www.fractalforums.com/ifs-iterated-function-systems/kaleidoscopic-(escape-time-ifs)/
    if (z.x+z.y<0.0) z.xy = -z.yx;
    if (z.x+z.z<0.0) z.xz = -z.zx;
    if (z.y+z.z<0.0) z.zy = -z.yz;

    z = (z*iterationScale - iterationOffset * (iterationScale-1.0));
    z.xy = rotate(z.xy, angleB);

    float iterationFactor = pow(iterationScale, -float(n+1));
    trapDistance = colorTrap(trapDistance, iterationFactor, z);
    pointDistance = min(pointDistance, trap(z) * iterationFactor);
  }
  return pointDistance;
}

//--------------------------------------------------------------------------------
// quaternion manipulation
//--------------------------------------------------------------------------------

vec4 qSquare( vec4 a ) {
    return vec4( a.x*a.x - dot(a.yzw,a.yzw), 2.0*a.x*(a.yzw) );
}

vec4 qCube( vec4 a ) {
  return a * ( 4.0*a.x*a.x - dot(a,a)*vec4(3.0,1.0,1.0,1.0) );
}

float lengthSquared( vec4 z ) { return dot(z,z); }
vec4 c = vec4(-0.1,0.6,0.9,-0.3) + 0.1*sin( vec4(3.0,0.0,1.0,2.0) + 0.5*vec4(1.0,1.3,1.7,2.1)*time);

vec3 Julia( vec3 p ) {
  vec4 z = vec4( p, 0.2 );

  float m2 = 0.0;
  vec2 t = vec2( 1e10 );

  float dz2 = 1.0;
  for( int i=0; i<10; i++ ) {
    // |dz|^2 = |3z^2|^2
    dz2 *= 9.0 * lengthSquared(qSquare(z));
    // z = z^3 + c
    z = qCube( z ) + c;

    // stop under divergence
    m2 = dot(z, z);
    if( m2>10000.0 ) break;

    // orbit trapping ( |z|^2 and z_x  )
    t = min( t, vec2( m2, abs(z.x)) );

  }

  // distance estimator: d(z) = 0.5 * log|z| * |z|/|dz|   (see http://iquilezles.org/www/articles/distancefractals/distancefractals.htm)
  float d = 0.25 * log(m2) * sqrt(m2 / dz2);

  return vec3( d, t );
}

vec3 Mandelbulb(vec3 p) {
  p.xyz = p.xzy;
  vec3 z = p;
  vec3 dz=vec3(0.0);
  float power = 8.0;
  float r, theta, phi;
  float dr = 1.0;

  float t0 = 1.0;

  for(int i = 0; i < 7; ++i) {
    r = length(z);
    if(r > 2.0) continue;
    theta = atan(z.y / z.x);
    phi = asin(z.z / r);

    dr = pow(r, power - 1.0) * dr * power + 1.0;

    r = pow(r, power);
    theta = theta * power;
    phi = phi * power;

    z = r * vec3(cos(theta)*cos(phi), sin(theta)*cos(phi), sin(phi)) + p;

    t0 = min(t0, r);
  }
  return vec3(0.5 * log(r) * r / dr, t0, 0.0);
}

// This should return continuous positive values when outside and negative values inside,
// which roughly indicate the distance of the nearest surface.
float Dist(vec3 pos, out vec3 trapDistance) {
   pos = RotateY(pos, time*0.025);

  switch(distanceEstimatorFunction) {
    case 1: return OctoKaleidoscopeIFS(pos, trapDistance);
    case 2: return TetraKaleidoscopeIFS(pos, trapDistance);
    // case 3: return Mandelbulb(pos).x;
  }
}

// Based on original by IQ - optimized to remove a divide
float CalcAO(vec3 p, vec3 n) {
   float r = 0.0;
   float w = 1.0;
   vec3 tmp;
   for (int i=1; i<=AO_SAMPLES; i++) {
      float d0 = float(i) * 0.3;
      r += w * (d0 - Dist(p + n * d0, tmp));
      w *= 0.5;
   }
   return 1.0 - clamp(r,0.0,1.0);
}

vec3 GetNormal(vec3 pos) {
   vec3 n;
   vec3 tmp;
   n.x = Dist(pos + delta.xyy, tmp) - Dist(pos - delta.xyy, tmp);
   n.y = Dist(pos + delta.yxy, tmp) - Dist(pos - delta.yxy, tmp);
   n.z = Dist(pos + delta.yyx, tmp) - Dist(pos - delta.yyx, tmp);

   return normalize(n);
}

float SoftShadow(vec3 ro, vec3 rd, float k)
{
   float res = 1.0;
   float t = 0.01;          // min-t see http://www.iquilezles.org/www/articles/rmshadows/rmshadows.htm
   vec3 tmp;
   for (int i=0; i<SHADOW_RAY_DEPTH; i++)
   {
      if (t < 25.0)  // max-t
      {
         float h = Dist(ro + rd * t, tmp);
         res = min(res, k*h/t);
         t += h;
      }
   }
   return clamp(res, 0.0, 1.0);
}

// Based on a shading method by Ben Weston. Added AO and SoftShadows to original.
vec4 Shading(vec3 pos, vec3 rd, vec3 norm, vec3 trapDistance) {
  vec3 hsvColor = rgb2hsv(normalize(trapDistance));
  float hue = mod(hsvColor.r * 1000 + sin(time * 0.025) * 2000, 1000) / 1000;
  vec3 color = hsv2rgb(vec3(hue, 0.6, 0.5));
  vec3 light = color * max(0.0, dot(norm, lightDir));

  light = (diffuse * light);
  light *= SoftShadow(pos, lightDir, 16.0);
  light += hsv2rgb(vec3(hue, 0.2, 0.6)) * CalcAO(pos, norm) * ambientFactor;
  return vec4(light, 1.0);
}

// Camera function by TekF
// Compute ray from camera parameters
vec3 GetRay(vec3 dir, vec2 pos) {
   pos = pos - 0.5;
   pos.x *= resolution.x/resolution.y;

   dir = normalize(dir);
   vec3 right = normalize(cross(vec3(0.,1.,0.),dir));
   vec3 up = normalize(cross(dir,right));

   return dir + right*pos.x + up*pos.y;
}

vec4 March(vec3 ro, vec3 rd, out vec3 trapDistance) {
   float t = 0.0;
   float d = 1.0;
   for (int i=0; i<RAY_DEPTH; i++)
   {
      vec3 p = ro + rd * t;
      d = Dist(p, trapDistance);
      if (abs(d) < DISTANCE_MIN)
      {
         return vec4(p, 1.0);
      }
      t += d;
      if (t >= MAX_DEPTH) break;
   }
   return vec4(0.0);
}

 // https://www.shadertoy.com/view/lt fSWn

void main() {
  const int ANTIALIAS_SAMPLES = 4;

  vec4 res = vec4(0.0);

  float d_ang = 2.*PI / float(ANTIALIAS_SAMPLES);
  float ang = d_ang * 0.33333;
  float r = 0.3;

  for (int i = 0; i < ANTIALIAS_SAMPLES; i++) {
     vec2 p = vec2((gl_FragCoord.x + cos(ang)*r) / resolution.x, (gl_FragCoord.y + sin(ang)*r) / resolution.y);
     vec3 ro = cameraPos;
     vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
     vec3 trapDistance;
     vec4 _res = March(ro, rd, trapDistance);

     if (_res.a == 1.0) {
        res.rgb += clamp(Shading(_res.rgb, rd, GetNormal(_res.rgb), trapDistance).rgb, 0.0, 1.0);
     } else {
        res.rgb = vec3(0.8, 0.95, 1.0) * (0.7 + 0.3 * rd.y);
        res.rgb += vec3(0.8, 0.7, 0.5) * pow(clamp(dot(rd, lightDir), 0.0, 1.0), 32.0);
     }
     ang += d_ang;
  }

  res.rgb /= float(ANTIALIAS_SAMPLES);

  gl_FragColor = vec4(res.rgb, 1.0);
}
