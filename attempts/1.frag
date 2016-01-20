uniform float time;
uniform vec2 resolution;
uniform vec3 cameraPos;
uniform vec3 cameraLookat;
uniform vec3 lightDir;
uniform vec3 lightColour;
uniform float specular;
uniform float specularHardness;
uniform vec3 diffuse;
uniform float ambientFactor;
uniform bool ao;
uniform bool shadows;
uniform bool rotateWorld;
uniform bool antialias;
uniform bool dof;

uniform int Iterations;
uniform float Scale;
uniform float Size;
uniform vec3 plnormal;
uniform vec3 Offset;
uniform float Angle1;
uniform vec3 Rot1;
uniform float Angle2;
uniform vec3 Rot2;

#define Phi (.5*(1.+sqrt(5.)))

vec3 n1 = normalize(vec3(-Phi,Phi-1.0,1.0));
vec3 n2 = normalize(vec3(1.0,-Phi,Phi+1.0));
vec3 n3 = normalize(vec3(0.0,0.0,-1.0));
mat4 M;

#define BAILOUT 1000.0
#define AO_SAMPLES 4
#define RAY_DEPTH 128
#define MAX_DEPTH 100.0
#define SHADOW_RAY_DEPTH 24
#define DISTANCE_MIN 0.0005
#define PI 3.14159265

const vec2 delta = vec2(0.0001, 0.);


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

// Icosahedral polyhedra Distance Estimator (Knighty 2011 some of the code is from Syntopia)
// Original DE can be found here: https://github.com/Syntopia/Fragmentarium/blob/master/Fragmentarium-Source/Examples/Knighty%20Collection/Icosahedral_polyhedra_iterated_20.frag
float Dist(vec3 z)
{
   if (rotateWorld) z = RotateY(z, sin(time*0.05)*PI);

   float dmin=10000.;
   float s=1.;
   for (int i=0; i<8; i++) {
      float t;
      // Folds. Dodecahedral
      z = abs(z);
      t=dot(z,n1); if (t>0.0) { z-=2.0*t*n1; }
      t=dot(z,n2); if (t>0.0) { z-=2.0*t*n2; }
      z = abs(z);
      t=dot(z,n1); if (t>0.0) { z-=2.0*t*n1; }
      t=dot(z,n2); if (t>0.0) { z-=2.0*t*n2; }
      z = abs(z);

      // Rotate, scale, rotate (we need to cast to a 4-component vector).
      z = (M*vec4(z,1.0)).xyz;
      s /= Scale;

      if (i == Iterations) break;
      if (dot(z,z) > BAILOUT) break;
   }
   //Distance to the plane going through vec3(Size,0.,0.) and which normal is plnormal
   return abs(s*dot(z-vec3(Size,0.,0.), plnormal));
}

// Based on original by IQ - optimized to remove a divide
float CalcAO(vec3 p, vec3 n)
{
   float r = 0.0;
   float w = 1.0;
   for (int i=1; i<=AO_SAMPLES; i++)
   {
      float d0 = float(i) * 0.3;
      r += w * (d0 - Dist(p + n * d0));
      w *= 0.5;
   }
   return 1.0 - clamp(r,0.0,1.0);
}

// Based on original code by IQ
float SoftShadow(vec3 ro, vec3 rd, float k)
{
   float res = 1.0;
   float t = 0.1;          // min-t see http://www.iquilezles.org/www/articles/rmshadows/rmshadows.htm
   for (int i=0; i<SHADOW_RAY_DEPTH; i++)
   {
      float h = Dist(ro + rd * t);
      res = min(res, k*h/t);
      t += h;
      if (t > 10.0) break; // max-t
   }
   return clamp(res, 0.0, 1.0);
}

vec3 GetNormal(vec3 pos)
{
   vec3 n;
   n.x = Dist( pos + delta.xyy ) - Dist( pos - delta.xyy );
   n.y = Dist( pos + delta.yxy ) - Dist( pos - delta.yxy );
   n.z = Dist( pos + delta.yyx ) - Dist( pos - delta.yyx );

   return normalize(n);
}

// Based on a shading method by Ben Weston. Added AO and SoftShadows to original.
vec4 Shading(vec3 pos, vec3 rd, vec3 norm)
{
   vec3 light = lightColour * max(0.0, dot(norm, lightDir));
   vec3 heading = normalize(-rd + lightDir);

   float spec = pow(max(0.0, dot(heading, norm)), specularHardness);
   light = (diffuse * light) + (spec * specular * lightColour);
   if (shadows) light *= SoftShadow(pos, lightDir, 16.0);
   if (ao) light += CalcAO(pos, norm) * ambientFactor;

   return vec4(light, 1.0);
}

// Original method by David Hoskins
vec3 Sky(in vec3 rd)
{
   float sunAmount = max(dot(rd, lightDir), 0.0);
   float v = pow(1.0 - max(rd.y,0.0),6.);
   vec3 sky = mix(vec3(.1, .2, .3), vec3(.32, .32, .32), v);
   sky += lightColour * sunAmount * sunAmount * .25 + lightColour * min(pow(sunAmount, 800.0)*1.5, .3);

   return clamp(sky, 0.0, 1.0);
}

// Camera function by TekF
// Compute ray from camera parameters
vec3 GetRay(vec3 dir, vec2 pos)
{
   pos = pos - 0.5;
   pos.x *= resolution.x/resolution.y;

   dir = normalize(dir);
   vec3 right = normalize(cross(vec3(0.,1.,0.),dir));
   vec3 up = normalize(cross(dir,right));

   return dir + right*pos.x + up*pos.y;
}

vec4 March(vec3 ro, vec3 rd)
{
   float t = 0.0;
   float d = 1.0;
   for (int i=0; i<RAY_DEPTH; i++)
   {
      vec3 p = ro + rd * t;
      d = Dist(p);
      if (abs(d) < DISTANCE_MIN)
      {
         return vec4(p, 1.0);
      }
      t += d;
      if (t >= MAX_DEPTH) break;
   }
   return vec4(0.0);
}

mat4 rotationMatrix(vec3 v, float angle)
{
   float c = cos(radians(angle));
   float s = sin(radians(angle));

   return mat4(c + (1.0 - c) * v.x * v.x, (1.0 - c) * v.x * v.y - s * v.z, (1.0 - c) * v.x * v.z + s * v.y, 0.0,
      (1.0 - c) * v.x * v.y + s * v.z, c + (1.0 - c) * v.y * v.y, (1.0 - c) * v.y * v.z - s * v.x, 0.0,
      (1.0 - c) * v.x * v.z - s * v.y, (1.0 - c) * v.y * v.z + s * v.x, c + (1.0 - c) * v.z * v.z, 0.0,
      0.0, 0.0, 0.0, 1.0);
}

mat4 translate(vec3 v) {
   return mat4(1.0,0.0,0.0,0.0,
      0.0,1.0,0.0,0.0,
      0.0,0.0,1.0,0.0,
      v.x,v.y,v.z,1.0);
}

mat4 scale4(float s) {
   return mat4(s,0.0,0.0,0.0,
      0.0,s,0.0,0.0,
      0.0,0.0,s,0.0,
      0.0,0.0,0.0,1.0);
}

void main()
{
   const int ANTIALIAS_SAMPLES = 4;
   const int DOF_SAMPLES = 8;

   // precalc - once...
   mat4 fracRotation2 = rotationMatrix(normalize(Rot2), Angle2);
   mat4 fracRotation1 = rotationMatrix(normalize(Rot1), Angle1);
   M = fracRotation2 * translate(Offset) * scale4(Scale) * translate(-Offset) * fracRotation1;

   vec4 res = vec4(0.0);

   if (antialias)
   {
      float d_ang = 2.*PI / float(ANTIALIAS_SAMPLES);
      float ang = d_ang * 0.33333;
      float r = 0.3;
      for (int i = 0; i < ANTIALIAS_SAMPLES; i++)
      {
         vec2 p = vec2((gl_FragCoord.x + cos(ang)*r) / resolution.x, (gl_FragCoord.y + sin(ang)*r) / resolution.y);
         vec3 ro = cameraPos;
         vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
         vec4 _res = March(ro, rd);
         if (_res.a == 1.0) res.xyz += clamp(Shading(_res.xyz, rd, GetNormal(_res.xyz)).xyz, 0.0, 1.0);
         else res.xyz += Sky(rd);
         ang += d_ang;
      }
      res.xyz /= float(ANTIALIAS_SAMPLES);
   }
   else if (dof)
   {
      vec2 p = gl_FragCoord.xy / resolution.xy;
      vec3 ro = cameraPos;
      vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
      vec4 _res = March(ro, rd);

      float d_ang = 2.*PI / float(DOF_SAMPLES);
      float ang = d_ang * 0.33333;
      // cheap DOF!
      float r = abs(cameraLookat.z - _res.z) * 3.0;
      for (int i = 0; i < DOF_SAMPLES; i++)
      {
         p = vec2((gl_FragCoord.x + cos(ang)*r) / resolution.x, (gl_FragCoord.y + sin(ang)*r) / resolution.y);
         ro = cameraPos;
         rd = normalize(GetRay(cameraLookat-cameraPos, p));
         _res = March(ro, rd);
         if (_res.a == 1.0) res.xyz += clamp(Shading(_res.xyz, rd, GetNormal(_res.xyz)).xyz, 0.0, 1.0);
         else res.xyz += Sky(rd);
         ang += d_ang;
      }
      res.xyz /= float(DOF_SAMPLES);
   }
   else
   {
      vec2 p = gl_FragCoord.xy / resolution.xy;
      vec3 ro = cameraPos;
      vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
      res = March(ro, rd);
      if (res.a == 1.0) res.xyz = clamp(Shading(res.xyz, rd, GetNormal(res.xyz)).xyz, 0.0, 1.0);
      else res.xyz = Sky(rd);
   }

   gl_FragColor = vec4(res.xyz, 1.0);
}
