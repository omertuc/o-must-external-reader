from flask import Flask
from flask import request
from pathlib import Path
import functools
import yaml
import json
import os

app = Flask(__name__)

os.chdir("gather")

@app.route("/apis/authorization.k8s.io/v1/selfsubjectaccessreviews", methods=["POST"])
def subject_access():
    print(request.json)
    return app.response_class(
        response="""
        {
          "kind": "SelfSubjectAccessReview",
          "apiVersion": "authorization.k8s.io/v1",
          "metadata": {
            "creationTimestamp": null
          },
          "spec": {
            "resourceAttributes": {
              "verb": "%s",
              "resource": "%s"
            }
          },
          "status": {
            "allowed": true,
            "reason": "Everyone can access the must-gather!"
          }
        }
        """ % (request.json["spec"]["resourceAttributes"]["verb"], request.json["spec"]["resourceAttributes"]["resource"]),
        status=200,
        mimetype='application/json'
    )

@app.route("/apis/<path:group_version>")
def specific_api(group_version):
    with (Path("../api_defs") / f"_apis_{group_version.replace('/', '_')}").open() as f:
        return f.read()

@app.route("/apis/<path:group_version>/namespaces/<path:namespace>/<path:resource>")
def apis_resource(group_version, namespace, resource):
    with (Path("namespaces") / namespace / group_version.split("/")[0] / f"{resource}.yaml").open("rb") as f:
        return app.response_class(
            response=json.dumps(yaml.safe_load(f)),
            status=200,
            mimetype='application/json'
        )

@app.route("/api/<path:_group_version>/namespaces/<path:namespace>/<path:resource>")
def api_resource(namespace, resource, _group_version):
    # mark unused
    _group_version = _group_version

    with (Path("namespaces") / namespace / "core" / f"{resource}.yaml").open("rb") as f:
        body = json.dumps(yaml.safe_load(f.read()))
        return app.response_class(
            response=body,
            status=200,
            mimetype='application/json'
        )

@app.route("/api/<path:_group_version>/namespaces/<path:namespace>/<path:resource>/<path:name>")
def api_resource_named(namespace, resource, name, _group_version):
    # mark unused
    _group_version = _group_version

    with (Path("namespaces") / namespace / "core" / f"{resource}.yaml").open("rb") as f:
        list = yaml.safe_load(f.read())
        for item in list["items"]:
            if item["metadata"]["name"] == name:
                return app.response_class(
                    response=json.dumps(item),
                    status=200,
                    mimetype='application/json'
                )

@app.route("/api/<path:_group_version>/namespaces/<path:namespace>/pods/<path:pod>/log")
def pod_container_logs(namespace, pod, _group_version):
    # mark unused
    _group_version = _group_version

    container = request.args["container"]

    with (Path("namespaces") / namespace / "pods" / pod / container / container / "logs" / "current.log").open("rb") as f:
        return app.response_class(
            response=f.read(),
            status=200,
            mimetype='application/json'
        )

@app.route("/api/<path:_group_version>/<path:resource>/<path:name>")
def api_cscoped_res(resource, name, _group_version):
    # mark unused
    _group_version = _group_version

    with (Path("cluster-scoped-resources") / "core" / f"{resource}" / f"{name}.yaml").open("rb") as f:
        return app.response_class(
            response=json.dumps(yaml.safe_load(f)),
            status=200,
            mimetype='application/json'
        )

@app.route("/apis/<path:group_version>/<path:_version>/<path:resource>")
def api_cscoped_custom(group_version, _version, resource):
    # mark unused
    cscoped_res_dir = Path("cluster-scoped-resources") / group_version / f"{resource}"
    if cscoped_res_dir.is_dir():
        resources = []
        for res in cscoped_res_dir.iterdir():
            try:
                with res.open("rb") as f:
                    resources.append(yaml.safe_load(f.read()))
            except Exception as e:
                print(f"Failed to load {res} {e}")
                pass

        resource_list = {
            "kind": f"{resources[0]['kind']}List",
            "apiVersion": "v1",
            "metadata": {
                "resourceVersion": "3790736",
            },
            "items": resources
        }

        return app.response_class(
            response=json.dumps(resource_list),
            status=200,
            mimetype='application/json'
        )
    else:
        all_items = []
        for namespace in Path("namespaces").iterdir():
            pods_path = (namespace / group_version / f"{resource}.yaml")
            if pods_path.is_file():
                with pods_path.open("rb") as f:
                    all_items.append(yaml.safe_load(f.read()))

        for i in range(1, len(all_items)):
            all_items[0]["items"].extend(all_items[i]["items"])

        return app.response_class(
            response=json.dumps(all_items[0]),
            status=200,
            mimetype='application/json'
        )

@app.route("/api/<path:_group_version>/<path:resource>")
def api_resource_all(resource, _group_version):
    # mark unused
    _group_version = _group_version

    cscoped_res_dir = Path("cluster-scoped-resources") / "core" / f"{resource}"
    if cscoped_res_dir.is_dir():
        resources = []
        for res in cscoped_res_dir.iterdir():
            with res.open("rb") as f:
                resources.append(yaml.safe_load(f.read()))

        resource_list = {
            "kind": f"{resources[0]['kind']}List",
            "apiVersion": "v1",
            "metadata": {
                "resourceVersion": "3790736",
            },
            "items": resources
        }

        return app.response_class(
            response=json.dumps(resource_list),
            status=200,
            mimetype='application/json'
        )
    else:
        all_items = []
        for namespace in Path("namespaces").iterdir():
            pods_path = (namespace / "core" / f"{resource}.yaml")
            if pods_path.is_file():
                with pods_path.open("rb") as f:
                    all_items.append(yaml.safe_load(f.read()))

        for i in range(1, len(all_items)):
            all_items[0]["items"].extend(all_items[i]["items"])

        return app.response_class(
            response=json.dumps(all_items[0]),
            status=200,
            mimetype='application/json'
        )

@app.route("/api/<path:_group_version>/namespaces")
def api_namespaces(_group_version):
    # mark unused
    _group_version = _group_version

    all_items = []
    for namespace in Path("namespaces").iterdir():
        ns_path = (namespace / f"{namespace.name}.yaml")
        if ns_path.is_file():
            with (namespace / f"{namespace.name}.yaml").open("rb") as f:
                all_items.append(yaml.safe_load(f.read()))

    namespaceList = {
        "kind": "NamespaceList",
        "apiVersion": "v1",
        "metadata": {
            "resourceVersion": "3790736",
        },
        "items": all_items
    }
    
    return app.response_class(
        response=json.dumps(namespaceList),
        status=200,
        mimetype='application/json'
    )

@app.route("/version")
def version():
    return app.response_class(
        response=r"""
        {
          "major": "1",
          "minor": "22",
          "gitVersion": "v1.22.3+ffbb954",
          "gitCommit": "3a0f2c90b43e6cffd07f57b5b78dd9f083e47ee2",
          "gitTreeState": "clean",
          "buildDate": "2021-11-29T05:06:16Z",
          "goVersion": "go1.16.6",
          "compiler": "gc",
          "platform": "linux/amd64"
        }""",
        status=200,
        mimetype='application/json'
    )

@app.route("/api")
def api():
    return app.response_class(
        response=r"""
            {
              "kind": "APIVersions",
              "versions": [
                "v1"
              ],
              "serverAddressByClientCIDRs": [
                {
                  "clientCIDR": "0.0.0.0/0",
                  "serverAddress": "localhost:5000"
                }
              ]
            }
""",
        status=200,
        mimetype='application/json'
    )

@app.route("/api/v1")
def api_v1():
    return app.response_class(
        response=r"""
{"kind":"APIResourceList","groupVersion":"v1","resources":[{"name":"bindings","singularName":"","namespaced":true,"kind":"Binding","verbs":["create"]},{"name":"componentstatuses","singularName":"","namespaced":false,"kind":"ComponentStatus","verbs":["get","list"],"shortNames":["cs"]},{"name":"configmaps","singularName":"","namespaced":true,"kind":"ConfigMap","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["cm"],"storageVersionHash":"qFsyl6wFWjQ="},{"name":"endpoints","singularName":"","namespaced":true,"kind":"Endpoints","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["ep"],"storageVersionHash":"fWeeMqaN/OA="},{"name":"events","singularName":"","namespaced":true,"kind":"Event","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["ev"],"storageVersionHash":"r2yiGXH7wu8="},{"name":"limitranges","singularName":"","namespaced":true,"kind":"LimitRange","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["limits"],"storageVersionHash":"EBKMFVe6cwo="},{"name":"namespaces","singularName":"","namespaced":false,"kind":"Namespace","verbs":["create","delete","get","list","patch","update","watch"],"shortNames":["ns"],"storageVersionHash":"Q3oi5N2YM8M="},{"name":"namespaces/finalize","singularName":"","namespaced":false,"kind":"Namespace","verbs":["update"]},{"name":"namespaces/status","singularName":"","namespaced":false,"kind":"Namespace","verbs":["get","patch","update"]},{"name":"nodes","singularName":"","namespaced":false,"kind":"Node","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["no"],"storageVersionHash":"XwShjMxG9Fs="},{"name":"nodes/proxy","singularName":"","namespaced":false,"kind":"NodeProxyOptions","verbs":["create","delete","get","patch","update"]},{"name":"nodes/status","singularName":"","namespaced":false,"kind":"Node","verbs":["get","patch","update"]},{"name":"persistentvolumeclaims","singularName":"","namespaced":true,"kind":"PersistentVolumeClaim","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["pvc"],"storageVersionHash":"QWTyNDq0dC4="},{"name":"persistentvolumeclaims/status","singularName":"","namespaced":true,"kind":"PersistentVolumeClaim","verbs":["get","patch","update"]},{"name":"persistentvolumes","singularName":"","namespaced":false,"kind":"PersistentVolume","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["pv"],"storageVersionHash":"HN/zwEC+JgM="},{"name":"persistentvolumes/status","singularName":"","namespaced":false,"kind":"PersistentVolume","verbs":["get","patch","update"]},{"name":"pods","singularName":"","namespaced":true,"kind":"Pod","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["po"],"categories":["all"],"storageVersionHash":"xPOwRZ+Yhw8="},{"name":"pods/attach","singularName":"","namespaced":true,"kind":"PodAttachOptions","verbs":["create","get"]},{"name":"pods/binding","singularName":"","namespaced":true,"kind":"Binding","verbs":["create"]},{"name":"pods/eviction","singularName":"","namespaced":true,"group":"policy","version":"v1","kind":"Eviction","verbs":["create"]},{"name":"pods/exec","singularName":"","namespaced":true,"kind":"PodExecOptions","verbs":["create","get"]},{"name":"pods/log","singularName":"","namespaced":true,"kind":"Pod","verbs":["get"]},{"name":"pods/portforward","singularName":"","namespaced":true,"kind":"PodPortForwardOptions","verbs":["create","get"]},{"name":"pods/proxy","singularName":"","namespaced":true,"kind":"PodProxyOptions","verbs":["create","delete","get","patch","update"]},{"name":"pods/status","singularName":"","namespaced":true,"kind":"Pod","verbs":["get","patch","update"]},{"name":"podtemplates","singularName":"","namespaced":true,"kind":"PodTemplate","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"storageVersionHash":"LIXB2x4IFpk="},{"name":"replicationcontrollers","singularName":"","namespaced":true,"kind":"ReplicationController","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["rc"],"categories":["all"],"storageVersionHash":"Jond2If31h0="},{"name":"replicationcontrollers/scale","singularName":"","namespaced":true,"group":"autoscaling","version":"v1","kind":"Scale","verbs":["get","patch","update"]},{"name":"replicationcontrollers/status","singularName":"","namespaced":true,"kind":"ReplicationController","verbs":["get","patch","update"]},{"name":"resourcequotas","singularName":"","namespaced":true,"kind":"ResourceQuota","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["quota"],"storageVersionHash":"8uhSgffRX6w="},{"name":"resourcequotas/status","singularName":"","namespaced":true,"kind":"ResourceQuota","verbs":["get","patch","update"]},{"name":"secrets","singularName":"","namespaced":true,"kind":"Secret","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"storageVersionHash":"S6u1pOWzb84="},{"name":"serviceaccounts","singularName":"","namespaced":true,"kind":"ServiceAccount","verbs":["create","delete","deletecollection","get","list","patch","update","watch"],"shortNames":["sa"],"storageVersionHash":"pbx9ZvyFpBE="},{"name":"serviceaccounts/token","singularName":"","namespaced":true,"group":"authentication.k8s.io","version":"v1","kind":"TokenRequest","verbs":["create"]},{"name":"services","singularName":"","namespaced":true,"kind":"Service","verbs":["create","delete","get","list","patch","update","watch"],"shortNames":["svc"],"categories":["all"],"storageVersionHash":"0/CO1lhkEBI="},{"name":"services/proxy","singularName":"","namespaced":true,"kind":"ServiceProxyOptions","verbs":["create","delete","get","patch","update"]},{"name":"services/status","singularName":"","namespaced":true,"kind":"Service","verbs":["get","patch","update"]}]}
""",
        status=200,
        mimetype='application/json'
    )

@app.route("/apis")
def apis():
    return app.response_class(
           response="{}",
           status=200,
           mimetype='application/json'
       )

pass
"""
{"kind":"APIGroupList","apiVersion":"v1","groups":[{"name":"apiregistration.k8s.io","versions":[{"groupVersion":"apiregistration.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"apiregistration.k8s.io/v1","version":"v1"}},{"name":"apps","versions":[{"groupVersion":"apps/v1","version":"v1"}],"preferredVersion":{"groupVersion":"apps/v1","version":"v1"}},{"name":"events.k8s.io","versions":[{"groupVersion":"events.k8s.io/v1","version":"v1"},{"groupVersion":"events.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"events.k8s.io/v1","version":"v1"}},{"name":"authentication.k8s.io","versions":[{"groupVersion":"authentication.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"authentication.k8s.io/v1","version":"v1"}},{"name":"authorization.k8s.io","versions":[{"groupVersion":"authorization.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"authorization.k8s.io/v1","version":"v1"}},{"name":"autoscaling","versions":[{"groupVersion":"autoscaling/v1","version":"v1"},{"groupVersion":"autoscaling/v2beta1","version":"v2beta1"},{"groupVersion":"autoscaling/v2beta2","version":"v2beta2"}],"preferredVersion":{"groupVersion":"autoscaling/v1","version":"v1"}},{"name":"batch","versions":[{"groupVersion":"batch/v1","version":"v1"},{"groupVersion":"batch/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"batch/v1","version":"v1"}},{"name":"certificates.k8s.io","versions":[{"groupVersion":"certificates.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"certificates.k8s.io/v1","version":"v1"}},{"name":"networking.k8s.io","versions":[{"groupVersion":"networking.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"networking.k8s.io/v1","version":"v1"}},{"name":"policy","versions":[{"groupVersion":"policy/v1","version":"v1"},{"groupVersion":"policy/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"policy/v1","version":"v1"}},{"name":"rbac.authorization.k8s.io","versions":[{"groupVersion":"rbac.authorization.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"rbac.authorization.k8s.io/v1","version":"v1"}},{"name":"storage.k8s.io","versions":[{"groupVersion":"storage.k8s.io/v1","version":"v1"},{"groupVersion":"storage.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"storage.k8s.io/v1","version":"v1"}},{"name":"admissionregistration.k8s.io","versions":[{"groupVersion":"admissionregistration.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"admissionregistration.k8s.io/v1","version":"v1"}},{"name":"apiextensions.k8s.io","versions":[{"groupVersion":"apiextensions.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"apiextensions.k8s.io/v1","version":"v1"}},{"name":"scheduling.k8s.io","versions":[{"groupVersion":"scheduling.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"scheduling.k8s.io/v1","version":"v1"}},{"name":"coordination.k8s.io","versions":[{"groupVersion":"coordination.k8s.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"coordination.k8s.io/v1","version":"v1"}},{"name":"node.k8s.io","versions":[{"groupVersion":"node.k8s.io/v1","version":"v1"},{"groupVersion":"node.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"node.k8s.io/v1","version":"v1"}},{"name":"discovery.k8s.io","versions":[{"groupVersion":"discovery.k8s.io/v1","version":"v1"},{"groupVersion":"discovery.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"discovery.k8s.io/v1","version":"v1"}},{"name":"flowcontrol.apiserver.k8s.io","versions":[{"groupVersion":"flowcontrol.apiserver.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"flowcontrol.apiserver.k8s.io/v1beta1","version":"v1beta1"}},{"name":"apps.openshift.io","versions":[{"groupVersion":"apps.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"apps.openshift.io/v1","version":"v1"}},{"name":"authorization.openshift.io","versions":[{"groupVersion":"authorization.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"authorization.openshift.io/v1","version":"v1"}},{"name":"build.openshift.io","versions":[{"groupVersion":"build.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"build.openshift.io/v1","version":"v1"}},{"name":"image.openshift.io","versions":[{"groupVersion":"image.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"image.openshift.io/v1","version":"v1"}},{"name":"oauth.openshift.io","versions":[{"groupVersion":"oauth.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"oauth.openshift.io/v1","version":"v1"}},{"name":"project.openshift.io","versions":[{"groupVersion":"project.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"project.openshift.io/v1","version":"v1"}},{"name":"quota.openshift.io","versions":[{"groupVersion":"quota.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"quota.openshift.io/v1","version":"v1"}},{"name":"route.openshift.io","versions":[{"groupVersion":"route.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"route.openshift.io/v1","version":"v1"}},{"name":"security.openshift.io","versions":[{"groupVersion":"security.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"security.openshift.io/v1","version":"v1"}},{"name":"template.openshift.io","versions":[{"groupVersion":"template.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"template.openshift.io/v1","version":"v1"}},{"name":"user.openshift.io","versions":[{"groupVersion":"user.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"user.openshift.io/v1","version":"v1"}},{"name":"packages.operators.coreos.com","versions":[{"groupVersion":"packages.operators.coreos.com/v1","version":"v1"}],"preferredVersion":{"groupVersion":"packages.operators.coreos.com/v1","version":"v1"}},{"name":"config.openshift.io","versions":[{"groupVersion":"config.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"config.openshift.io/v1","version":"v1"}},{"name":"operator.openshift.io","versions":[{"groupVersion":"operator.openshift.io/v1","version":"v1"},{"groupVersion":"operator.openshift.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"operator.openshift.io/v1","version":"v1"}},{"name":"apiserver.openshift.io","versions":[{"groupVersion":"apiserver.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"apiserver.openshift.io/v1","version":"v1"}},{"name":"autoscaling.openshift.io","versions":[{"groupVersion":"autoscaling.openshift.io/v1","version":"v1"},{"groupVersion":"autoscaling.openshift.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"autoscaling.openshift.io/v1","version":"v1"}},{"name":"cloudcredential.openshift.io","versions":[{"groupVersion":"cloudcredential.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"cloudcredential.openshift.io/v1","version":"v1"}},{"name":"console.openshift.io","versions":[{"groupVersion":"console.openshift.io/v1","version":"v1"},{"groupVersion":"console.openshift.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"console.openshift.io/v1","version":"v1"}},{"name":"imageregistry.operator.openshift.io","versions":[{"groupVersion":"imageregistry.operator.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"imageregistry.operator.openshift.io/v1","version":"v1"}},{"name":"ingress.operator.openshift.io","versions":[{"groupVersion":"ingress.operator.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"ingress.operator.openshift.io/v1","version":"v1"}},{"name":"k8s.cni.cncf.io","versions":[{"groupVersion":"k8s.cni.cncf.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"k8s.cni.cncf.io/v1","version":"v1"}},{"name":"machineconfiguration.openshift.io","versions":[{"groupVersion":"machineconfiguration.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"machineconfiguration.openshift.io/v1","version":"v1"}},{"name":"monitoring.coreos.com","versions":[{"groupVersion":"monitoring.coreos.com/v1","version":"v1"},{"groupVersion":"monitoring.coreos.com/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"monitoring.coreos.com/v1","version":"v1"}},{"name":"network.openshift.io","versions":[{"groupVersion":"network.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"network.openshift.io/v1","version":"v1"}},{"name":"network.operator.openshift.io","versions":[{"groupVersion":"network.operator.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"network.operator.openshift.io/v1","version":"v1"}},{"name":"operators.coreos.com","versions":[{"groupVersion":"operators.coreos.com/v2","version":"v2"},{"groupVersion":"operators.coreos.com/v1","version":"v1"},{"groupVersion":"operators.coreos.com/v1alpha2","version":"v1alpha2"},{"groupVersion":"operators.coreos.com/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"operators.coreos.com/v2","version":"v2"}},{"name":"samples.operator.openshift.io","versions":[{"groupVersion":"samples.operator.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"samples.operator.openshift.io/v1","version":"v1"}},{"name":"security.internal.openshift.io","versions":[{"groupVersion":"security.internal.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"security.internal.openshift.io/v1","version":"v1"}},{"name":"snapshot.storage.k8s.io","versions":[{"groupVersion":"snapshot.storage.k8s.io/v1","version":"v1"},{"groupVersion":"snapshot.storage.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"snapshot.storage.k8s.io/v1","version":"v1"}},{"name":"tuned.openshift.io","versions":[{"groupVersion":"tuned.openshift.io/v1","version":"v1"}],"preferredVersion":{"groupVersion":"tuned.openshift.io/v1","version":"v1"}},{"name":"controlplane.operator.openshift.io","versions":[{"groupVersion":"controlplane.operator.openshift.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"controlplane.operator.openshift.io/v1alpha1","version":"v1alpha1"}},{"name":"metal3.io","versions":[{"groupVersion":"metal3.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"metal3.io/v1alpha1","version":"v1alpha1"}},{"name":"migration.k8s.io","versions":[{"groupVersion":"migration.k8s.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"migration.k8s.io/v1alpha1","version":"v1alpha1"}},{"name":"whereabouts.cni.cncf.io","versions":[{"groupVersion":"whereabouts.cni.cncf.io/v1alpha1","version":"v1alpha1"}],"preferredVersion":{"groupVersion":"whereabouts.cni.cncf.io/v1alpha1","version":"v1alpha1"}},{"name":"helm.openshift.io","versions":[{"groupVersion":"helm.openshift.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"helm.openshift.io/v1beta1","version":"v1beta1"}},{"name":"machine.openshift.io","versions":[{"groupVersion":"machine.openshift.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"machine.openshift.io/v1beta1","version":"v1beta1"}},{"name":"metrics.k8s.io","versions":[{"groupVersion":"metrics.k8s.io/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"metrics.k8s.io/v1beta1","version":"v1beta1"}}]}
"""



