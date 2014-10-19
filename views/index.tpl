<script type="text/javascript">
function post_analyze(path) {
    var form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', '/analyze/?path=' + path);
    form.style.display = 'hidden';
    document.body.appendChild(form)
    form.submit();
}
</script>

%for path, img_count in tracks:
    <p>
        {{path}}:
        %if img_count:
            <a href="/view/{{path}}">View plots</a>
            <button type="button" onclick="post_analyze('{{path}}');" style="font-size: 60%;">Re-analyze</button>
        %else:
            <button type="button" onclick="post_analyze('{{path}}');">Analyze</button>
        %end
    </p>
%end
